<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { isLoggedIn, isPro, user, logout } from '../auth.js'
import { getScoreHistory, getUserScans } from '../api.js'

const route = useRoute()
const router = useRouter()

const domain = ref(route.params.domain || '')
const history = ref([])
const domains = ref([])
const loading = ref(true)
const error = ref('')

function handleLogout() {
  logout()
  router.push('/')
}

function gradeFor(score) {
  if (score >= 90) return 'A+'
  if (score >= 80) return 'A'
  if (score >= 70) return 'B'
  if (score >= 60) return 'C'
  if (score >= 40) return 'D'
  return 'F'
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

async function fetchHistory() {
  if (!domain.value) {
    loading.value = false
    return
  }
  loading.value = true
  error.value = ''
  try {
    history.value = await getScoreHistory(domain.value)
  } catch (e) {
    error.value = e.message || 'Could not load history.'
  } finally {
    loading.value = false
  }
}

function selectDomain(d) {
  domain.value = d
  router.replace({ name: 'History', params: { domain: d } })
}

watch(() => domain.value, fetchHistory)

onMounted(async () => {
  // Load user's scanned domains for the selector
  try {
    const scans = await getUserScans()
    const unique = [...new Set(scans.map(s => s.domain))]
    domains.value = unique
    if (!domain.value && unique.length > 0) {
      domain.value = unique[0]
      router.replace({ name: 'History', params: { domain: unique[0] } })
    }
  } catch {
    // non-critical
  }

  if (domain.value) {
    await fetchHistory()
  } else {
    loading.value = false
  }
})
</script>

<template>
  <div class="flex-1 flex flex-col">
    <!-- Nav -->
    <nav class="sticky top-0 z-50 bg-page/95 backdrop-blur-sm border-b border-border-light">
      <div class="max-w-5xl mx-auto px-6 lg:px-8 h-14 flex items-center justify-between">
        <router-link to="/" class="flex items-center gap-2">
          <svg class="w-5 h-5 text-accent" viewBox="0 0 24 24" fill="none">
            <path d="M12 2L4 20h4l1.5-4h5L16 20h4L12 2zm0 7l2 5h-4l2-5z" fill="currentColor"/>
            <path d="M20 8a10 10 0 00-4-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" opacity="0.5"/>
            <path d="M22 6a14 14 0 00-6-5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" opacity="0.3"/>
          </svg>
          <span class="font-display font-bold text-[15px] tracking-tight">AgentReady</span>
        </router-link>
        <div class="flex items-center gap-4">
          <router-link to="/dashboard" class="text-[13px] text-secondary hover:text-primary transition-colors">Dashboard</router-link>
          <router-link to="/monitoring" class="text-[13px] text-secondary hover:text-primary transition-colors">Monitoring</router-link>
          <button @click="handleLogout" class="btn-ghost text-[13px]">Sign out</button>
          <div
            class="w-7 h-7 rounded-full bg-accent text-white flex items-center justify-center text-xs font-display font-bold"
            :title="user?.email"
          >
            {{ user?.email?.[0]?.toUpperCase() || '?' }}
          </div>
        </div>
      </div>
    </nav>

    <!-- Content -->
    <div class="flex-1">
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
          <!-- Domain selector -->
          <div v-if="domains.length > 1" class="mb-6">
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

          <!-- No domain selected -->
          <div v-else-if="!domain" class="border border-border-light rounded-lg p-8 text-center">
            <p class="text-sm text-secondary">Run a scan first to see score history.</p>
            <router-link to="/" class="btn-primary mt-3 inline-block">Run a scan</router-link>
          </div>

          <!-- Empty history -->
          <div v-else-if="history.length === 0" class="border border-border-light rounded-lg p-8 text-center">
            <p class="text-sm text-secondary">No history data for {{ domain }} yet.</p>
          </div>

          <!-- History chart + table -->
          <div v-else>
            <!-- Simple CSS bar chart -->
            <div class="mb-8">
              <p class="section-label mb-4">Score over time for {{ domain }}</p>
              <div class="flex items-end gap-2 h-32">
                <div
                  v-for="(entry, idx) in history"
                  :key="idx"
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
                    {{ formatDate(entry.date || entry.created_at).replace(/, \d{4}$/, '') }}
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
                    v-for="(entry, idx) in history"
                    :key="idx"
                    class="border-b border-border-light last:border-b-0"
                  >
                    <td class="px-5 py-3 text-secondary">{{ formatDate(entry.date || entry.created_at) }}</td>
                    <td class="px-5 py-3">
                      <span class="font-display font-semibold tabular-nums" :class="scoreColorClass(entry.score)">{{ entry.score }}</span>
                    </td>
                    <td class="px-5 py-3 text-secondary font-display">{{ entry.grade || gradeFor(entry.score) }}</td>
                    <td class="px-5 py-3 text-right">
                      <router-link
                        v-if="entry.scan_id"
                        :to="{ name: 'Report', params: { id: entry.scan_id } }"
                        class="text-[13px] text-accent hover:text-accent-hover transition-colors"
                      >
                        View report
                      </router-link>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Footer -->
    <footer class="border-t border-border-light py-6 px-6 lg:px-8 mt-auto">
      <div class="max-w-5xl mx-auto flex items-center justify-between">
        <span class="text-xs text-muted">&copy; {{ new Date().getFullYear() }} AgentReady</span>
        <a
          href="https://github.com/lennystepn-hue/agentready"
          target="_blank"
          rel="noopener"
          class="text-xs text-secondary hover:text-primary transition-colors"
        >
          GitHub
        </a>
      </div>
    </footer>
  </div>
</template>
