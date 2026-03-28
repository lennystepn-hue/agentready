<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { isLoggedIn, isPro, user, logout } from '../auth.js'
import { getUserScans } from '../api.js'
import AppLayout from '../components/AppLayout.vue'

const route = useRoute()
const router = useRouter()

const domain = ref(route.params.domain || '')
const allScans = ref([])
const loading = ref(true)
const error = ref('')

function gradeFor(score) {
  if (score >= 90) return 'A+'
  if (score >= 80) return 'A'
  if (score >= 70) return 'B'
  if (score >= 60) return 'C'
  if (score >= 40) return 'D'
  return 'F'
}

function normalizeScan(s) {
  return {
    scan_id: s.scan_id || s.id,
    domain: s.domain || '',
    score: s.score ?? s.total_score ?? null,
    grade: s.grade || gradeFor(s.score ?? s.total_score ?? null),
    status: s.status || 'unknown',
    created_at: s.created_at || s.completed_at || '',
  }
}

function scoreColorClass(score) {
  if (score >= 70) return 'text-score-good'
  if (score >= 40) return 'text-score-medium'
  return 'text-score-bad'
}

function barColorClass(score) {
  if (score >= 70) return 'bg-score-good'
  if (score >= 40) return 'bg-score-medium'
  return 'bg-score-bad'
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric',
  })
}

// Group scans by domain
const scansByDomain = computed(() => {
  const map = {}
  for (const s of allScans.value) {
    if (!s.domain) continue
    if (!map[s.domain]) map[s.domain] = []
    map[s.domain].push(s)
  }
  // Sort each group by date descending
  for (const d of Object.keys(map)) {
    map[d].sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
  }
  return map
})

// Unique domains sorted by most recent scan first
const domains = computed(() => {
  const entries = Object.entries(scansByDomain.value)
  entries.sort((a, b) => {
    const dateA = a[1][0]?.created_at || ''
    const dateB = b[1][0]?.created_at || ''
    return new Date(dateB) - new Date(dateA)
  })
  return entries.map(([d]) => d)
})

// Scans for the currently selected domain
const history = computed(() => {
  if (!domain.value) return []
  return scansByDomain.value[domain.value] || []
})

function selectDomain(d) {
  domain.value = d
  router.replace({ name: 'History', params: { domain: d } })
}

onMounted(async () => {
  try {
    const data = await getUserScans()
    const raw = Array.isArray(data) ? data : (data.scans || [])
    allScans.value = raw.map(normalizeScan)

    // Auto-select domain if none specified
    if (!domain.value && domains.value.length > 0) {
      domain.value = domains.value[0]
      router.replace({ name: 'History', params: { domain: domains.value[0] } })
    }
  } catch (e) {
    error.value = e.message || 'Could not load scans.'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <AppLayout>
    <div class="flex-1 pb-16 sm:pb-0">
      <div class="max-w-5xl mx-auto px-6 lg:px-8 py-10">

        <div class="animate-fade-in mb-8">
          <p class="section-label mb-2">Pro feature</p>
          <h1 class="font-display text-2xl font-bold tracking-tight text-primary">Score history</h1>
          <p class="text-sm text-secondary mt-2 leading-relaxed max-w-lg">
            Track how your AI agent readiness score changes over time.
          </p>
        </div>

        <!-- Pro gate -->
        <div v-if="!isPro" class="border border-accent/20 rounded-lg p-8 bg-accent/[0.03] text-center animate-slide-up">
          <h3 class="font-display font-semibold text-primary mb-2">Pro feature</h3>
          <p class="text-sm text-secondary mb-4 max-w-sm mx-auto">
            Score history is available on the Pro plan. Upgrade to see how your readiness improves over time.
          </p>
          <router-link to="/pricing" class="btn-primary">Upgrade to Pro</router-link>
        </div>

        <!-- History content -->
        <div v-else class="animate-slide-up">
          <!-- Loading -->
          <div v-if="loading" class="py-8 text-center">
            <svg class="w-5 h-5 text-accent animate-spin mx-auto mb-2" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            <p class="text-sm text-muted">Loading history...</p>
          </div>

          <div v-else-if="error" class="py-8 text-center">
            <p class="text-sm text-score-bad">{{ error }}</p>
          </div>

          <!-- No scans at all -->
          <div v-else-if="allScans.length === 0" class="border border-border-light rounded-lg p-8 text-center">
            <p class="text-sm text-secondary mb-1">You haven't scanned any domains yet.</p>
            <p class="text-sm text-muted mb-4">Run a scan to start tracking your score over time.</p>
            <router-link to="/" class="btn-primary inline-block">Run a scan</router-link>
          </div>

          <!-- Has scans -->
          <div v-else>
            <!-- Domain selector -->
            <div class="mb-6">
              <p class="section-label mb-2">Select domain</p>
              <div class="flex flex-wrap gap-2">
                <button
                  v-for="d in domains"
                  :key="d"
                  @click="selectDomain(d)"
                  class="px-3 py-1.5 text-sm font-display rounded-md border transition-colors"
                  :class="d === domain ? 'border-accent bg-accent-light text-accent font-semibold' : 'border-border text-secondary hover:bg-warm-100'"
                >
                  {{ d }}
                </button>
              </div>
            </div>

            <!-- Empty history for this domain -->
            <div v-if="history.length === 0" class="border border-border-light rounded-lg p-8 text-center">
              <p class="text-sm text-secondary">No history data for {{ domain }} yet.</p>
            </div>

            <!-- History chart + table -->
            <div v-else>
              <!-- Simple CSS bar chart -->
              <div class="mb-8">
                <p class="section-label mb-4">Score over time for {{ domain }}</p>
                <div class="flex items-end gap-2 h-32">
                  <div
                    v-for="(entry, idx) in [...history].reverse()"
                    :key="entry.scan_id || idx"
                    class="flex-1 flex flex-col items-center justify-end gap-1 min-w-0"
                  >
                    <span class="text-[11px] font-display font-semibold tabular-nums" :class="scoreColorClass(entry.score)">
                      {{ entry.score }}
                    </span>
                    <div
                      class="w-full max-w-[40px] rounded-t transition-all duration-500"
                      :class="barColorClass(entry.score)"
                      :style="{ height: Math.max(4, entry.score) + '%' }"
                    />
                    <span class="text-[9px] text-muted truncate max-w-full">
                      {{ formatDate(entry.created_at).replace(/, \d{4}$/, '') }}
                    </span>
                  </div>
                </div>
              </div>

              <!-- Table -->
              <div class="border border-border rounded-lg overflow-hidden bg-surface">
                <table class="w-full text-left text-sm">
                  <thead>
                    <tr class="border-b border-border-light">
                      <th class="px-5 py-3 text-xs font-display font-semibold text-muted uppercase tracking-wider">Date</th>
                      <th class="px-5 py-3 text-xs font-display font-semibold text-muted uppercase tracking-wider">Score</th>
                      <th class="px-5 py-3 text-xs font-display font-semibold text-muted uppercase tracking-wider">Grade</th>
                      <th class="px-5 py-3 text-xs font-display font-semibold text-muted uppercase tracking-wider"></th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr
                      v-for="entry in history"
                      :key="entry.scan_id"
                      class="border-b border-border-light last:border-b-0"
                    >
                      <td class="px-5 py-3 text-secondary">{{ formatDate(entry.created_at) }}</td>
                      <td class="px-5 py-3">
                        <span class="font-display font-semibold tabular-nums" :class="scoreColorClass(entry.score)">{{ entry.score }}</span>
                      </td>
                      <td class="px-5 py-3 text-secondary font-display">{{ entry.grade }}</td>
                      <td class="px-5 py-3 text-right">
                        <router-link
                          v-if="entry.scan_id && entry.status === 'completed'"
                          :to="{ name: 'Report', params: { id: entry.scan_id } }"
                          class="text-[13px] text-accent hover:text-accent-hover transition-colors"
                        >
                          View report
                        </router-link>
                        <span v-else-if="entry.status && entry.status !== 'completed'" class="text-[13px] text-muted">
                          {{ entry.status }}
                        </span>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </AppLayout>
</template>
