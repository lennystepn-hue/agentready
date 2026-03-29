<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { isLoggedIn, isPro, user } from '../auth.js'
import { getUserScans, getMonitors, startScan } from '../api.js'
import ScoreCircle from '../components/ScoreCircle.vue'
import AppLayout from '../components/AppLayout.vue'
import UpgradeCard from '../components/UpgradeCard.vue'

const router = useRouter()

const scans = ref([])
const monitors = ref([])
const loadingScans = ref(true)
const loadingMonitors = ref(false)
const error = ref('')
const scanDomain = ref('')
const scanning = ref(false)

async function handleScan() {
  if (!scanDomain.value.trim()) return
  scanning.value = true
  try {
    const result = await startScan(scanDomain.value.trim())
    router.push({ name: 'ScanProgress', params: { id: result.scan_id } })
  } catch (e) {
    error.value = e.message || 'Could not start scan.'
  } finally {
    scanning.value = false
  }
}

function gradeFor(score) {
  if (score == null) return '—'
  if (score >= 90) return 'A+'
  if (score >= 80) return 'A'
  if (score >= 70) return 'B'
  if (score >= 60) return 'C'
  if (score >= 40) return 'D'
  if (score >= 20) return 'E'
  return 'F'
}

function scoreColorClass(score) {
  if (score == null) return 'text-muted'
  if (score >= 70) return 'text-score-good'
  if (score >= 40) return 'text-score-medium'
  return 'text-score-bad'
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric',
  })
}

function normalizeScan(s) {
  return {
    scan_id: s.scan_id || s.id,
    domain: s.domain || '',
    score: s.score ?? s.total_score ?? null,
    grade: s.grade || gradeFor(s.score ?? s.total_score ?? null),
    status: s.status || 'unknown',
    created_at: s.created_at || s.completed_at || '',
    site_type: s.site_type || s.site_label || null,
  }
}

const completedScans = computed(() =>
  scans.value.filter(s => s.status === 'completed' && s.score != null)
)

const bestScan = computed(() => {
  if (completedScans.value.length === 0) return null
  return completedScans.value.reduce((a, b) => (a.score > b.score ? a : b))
})

const avgScore = computed(() => {
  if (completedScans.value.length === 0) return null
  const sum = completedScans.value.reduce((a, b) => a + b.score, 0)
  return Math.round(sum / completedScans.value.length)
})

const uniqueDomains = computed(() => {
  const domains = new Set(completedScans.value.map(s => s.domain))
  return domains.size
})

const recentScans = computed(() => scans.value.slice(0, 10))

const proFeatures = [
  { title: 'Competitor Compare', desc: 'Side-by-side analysis of up to 4 domains.', to: '/compare' },
  { title: 'Monitoring', desc: 'Weekly re-scans and score change alerts.', to: '/monitoring' },
  { title: 'Score History', desc: 'Track your score improvements over time.', to: '/history' },
  {
    title: 'AI Discovery',
    desc: 'Check if AI agents actually recommend your site.',
    to: computed(() =>
      completedScans.value.length > 0
        ? { name: 'Report', params: { id: completedScans.value[0].scan_id }, hash: '#discovery' }
        : '/'
    ),
  },
]

onMounted(async () => {
  try {
    const data = await getUserScans()
    const raw = Array.isArray(data) ? data : (data.scans || [])
    scans.value = raw.map(normalizeScan)
  } catch (e) {
    error.value = e.message || 'Could not load scans.'
  } finally {
    loadingScans.value = false
  }

  if (isPro.value) {
    loadingMonitors.value = true
    try {
      const data = await getMonitors()
      monitors.value = Array.isArray(data) ? data : (data.monitors || [])
    } catch {
      // non-critical
    } finally {
      loadingMonitors.value = false
    }
  }
})
</script>

<template>
  <AppLayout>
    <div class="flex-1 pb-16 sm:pb-0">

      <!-- 1. Hero / Status Area -->
      <div class="border-b border-border-light bg-warm-50">
        <div class="max-w-5xl mx-auto px-6 lg:px-8 py-10 animate-fade-in">
          <template v-if="!loadingScans && completedScans.length > 0">
            <div class="flex flex-col sm:flex-row items-center gap-6">
              <ScoreCircle :score="bestScan.score" :size="120" />
              <div>
                <h1 class="font-display text-2xl font-bold tracking-tight text-primary">Your AI Visibility</h1>
                <p v-if="isPro" class="text-sm text-secondary mt-1 max-w-md">
                  AI agents are learning about your sites. Keep improving.
                </p>
                <p v-else class="text-sm text-secondary mt-1 max-w-md">
                  Your sites may be invisible to AI agents. Upgrade to fix that.
                </p>
                <div class="flex items-center gap-2 mt-2">
                  <span
                    class="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-display font-bold uppercase tracking-wider"
                    :class="isPro ? 'bg-accent text-white' : 'bg-warm-200 text-warm-600'"
                  >
                    {{ isPro ? 'Pro' : 'Free' }}
                  </span>
                  <span class="text-xs text-muted">{{ user?.email }}</span>
                </div>
              </div>
            </div>
          </template>
          <template v-else-if="!loadingScans">
            <h1 class="font-display text-2xl font-bold tracking-tight text-primary">Welcome to AgentCheck</h1>
            <p class="text-sm text-secondary mt-1 max-w-md">
              Run your first scan to see how visible your site is to AI agents.
            </p>
            <div class="flex items-center gap-2 mt-3">
              <span
                class="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-display font-bold uppercase tracking-wider"
                :class="isPro ? 'bg-accent text-white' : 'bg-warm-200 text-warm-600'"
              >
                {{ isPro ? 'Pro' : 'Free' }}
              </span>
              <span class="text-xs text-muted">{{ user?.email }}</span>
            </div>
          </template>
          <template v-else>
            <div class="h-20 flex items-center">
              <svg class="w-5 h-5 text-accent animate-spin" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
            </div>
          </template>
        </div>
      </div>

      <div class="max-w-5xl mx-auto px-6 lg:px-8 py-8">

        <!-- 2. Inline Scan Bar -->
        <section class="mb-10 animate-slide-up">
          <form @submit.prevent="handleScan" class="flex gap-3">
            <input
              v-model="scanDomain"
              type="text"
              placeholder="Enter a domain to scan..."
              class="input-field flex-1 text-sm"
            />
            <button
              type="submit"
              class="btn-primary text-sm px-6 shrink-0"
              :disabled="scanning || !scanDomain.trim()"
            >
              {{ scanning ? 'Scanning...' : 'Run scan' }}
            </button>
          </form>
          <p v-if="error" class="text-sm text-score-bad mt-2">{{ error }}</p>
        </section>

        <!-- 3. Stats Row -->
        <section v-if="completedScans.length > 0" class="mb-10 animate-slide-up" style="animation-delay: 60ms">
          <div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div class="border border-border rounded-lg p-5 bg-surface">
              <p class="text-xs text-muted font-display uppercase tracking-wider mb-2">Total scans</p>
              <p class="font-display text-2xl font-bold text-primary tabular-nums">{{ completedScans.length }}</p>
            </div>
            <div class="border border-border rounded-lg p-5 bg-surface">
              <p class="text-xs text-muted font-display uppercase tracking-wider mb-2">Average score</p>
              <p class="font-display text-2xl font-bold tabular-nums" :class="scoreColorClass(avgScore)">{{ avgScore }}</p>
            </div>
            <div class="border border-border rounded-lg p-5 bg-surface">
              <p class="text-xs text-muted font-display uppercase tracking-wider mb-2">Best score</p>
              <p class="font-display text-2xl font-bold tabular-nums" :class="scoreColorClass(bestScan?.score)">
                {{ bestScan?.score ?? '—' }}
              </p>
            </div>
            <div class="border border-border rounded-lg p-5 bg-surface">
              <p class="text-xs text-muted font-display uppercase tracking-wider mb-2">Sites monitored</p>
              <p class="font-display text-2xl font-bold text-primary tabular-nums">
                {{ isPro ? monitors.length : '—' }}
              </p>
            </div>
          </div>
        </section>

        <!-- 4. Recent Scans -->
        <section class="mb-10 animate-slide-up" style="animation-delay: 120ms">
          <div class="flex items-center justify-between mb-4">
            <h2 class="font-display text-lg font-bold tracking-tight">Recent scans</h2>
            <router-link to="/" class="text-[13px] text-accent hover:text-accent-hover transition-colors font-display font-medium">
              + New scan
            </router-link>
          </div>

          <div v-if="loadingScans" class="py-12 text-center">
            <svg class="w-5 h-5 text-accent animate-spin mx-auto mb-2" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            <p class="text-sm text-muted">Loading scans...</p>
          </div>

          <div v-else-if="scans.length === 0" class="border border-dashed border-border rounded-lg p-10 text-center">
            <p class="font-display font-semibold text-primary mb-1">No scans yet</p>
            <p class="text-sm text-secondary mb-5">Run your first scan to see how your site performs with AI agents.</p>
            <button @click="$refs.domainInput?.focus()" class="btn-primary px-6">
              Run a scan
            </button>
          </div>

          <div v-else class="space-y-2">
            <router-link
              v-for="scan in recentScans"
              :key="scan.scan_id"
              :to="scan.status === 'completed' ? { name: 'Report', params: { id: scan.scan_id } } : { name: 'ScanProgress', params: { id: scan.scan_id } }"
              class="flex items-center gap-5 px-5 py-4 border border-border rounded-lg bg-surface hover:border-warm-300 transition-colors group cursor-pointer"
            >
              <!-- Score circle or spinner -->
              <div class="flex-shrink-0 w-12 h-12 flex items-center justify-center">
                <ScoreCircle v-if="scan.status === 'completed' && scan.score != null" :score="scan.score" :size="48" />
                <div v-else-if="scan.status === 'pending' || scan.status === 'running'" class="w-10 h-10 rounded-full border-2 border-accent/30 flex items-center justify-center">
                  <svg class="w-5 h-5 text-accent animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                </div>
                <div v-else class="w-10 h-10 rounded-full border-2 border-score-bad/30 flex items-center justify-center">
                  <span class="text-xs text-score-bad font-display font-bold">ERR</span>
                </div>
              </div>

              <!-- Info -->
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 flex-wrap">
                  <p class="text-sm font-display font-semibold text-primary truncate group-hover:text-accent transition-colors">
                    {{ scan.domain }}
                  </p>
                  <span
                    v-if="scan.site_type"
                    class="text-[10px] font-display font-medium uppercase tracking-wider text-warm-500 bg-warm-100 px-1.5 py-0.5 rounded"
                  >
                    {{ scan.site_type }}
                  </span>
                  <span
                    v-if="scan.status === 'completed' && scan.score != null"
                    class="text-xs font-display font-bold px-1.5 py-0.5 rounded"
                    :class="{
                      'bg-score-good/10 text-score-good': scan.score >= 70,
                      'bg-score-medium/10 text-score-medium': scan.score >= 40 && scan.score < 70,
                      'bg-score-bad/10 text-score-bad': scan.score < 40,
                    }"
                  >
                    {{ scan.grade }}
                  </span>
                  <span
                    v-else-if="scan.status === 'running' || scan.status === 'pending'"
                    class="text-[11px] font-display text-accent bg-accent/10 px-1.5 py-0.5 rounded"
                  >
                    Scanning...
                  </span>
                </div>
                <p class="text-xs text-muted mt-0.5">
                  <span v-if="scan.created_at">{{ formatDate(scan.created_at) }}</span>
                </p>
              </div>

              <!-- Arrow -->
              <svg class="w-4 h-4 text-warm-300 group-hover:text-accent transition-colors flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
              </svg>
            </router-link>
          </div>
        </section>

        <!-- 5. Pro Features Section -->
        <section class="mb-10 animate-slide-up" style="animation-delay: 160ms">
          <!-- Free users: UpgradeCard -->
          <UpgradeCard v-if="!isPro" />

          <!-- Pro users: 2x2 feature grid -->
          <div v-else class="grid sm:grid-cols-2 gap-4">
            <router-link
              v-for="feat in proFeatures"
              :key="feat.title"
              :to="typeof feat.to === 'object' && feat.to?.value !== undefined ? feat.to.value : feat.to"
              class="border border-border rounded-lg p-5 bg-surface hover:border-warm-300 transition-colors group"
            >
              <div class="flex items-center justify-between">
                <h4 class="font-display font-semibold text-sm text-primary group-hover:text-accent transition-colors">
                  {{ feat.title }}
                </h4>
                <svg class="w-4 h-4 text-warm-300 group-hover:text-accent transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
                </svg>
              </div>
              <p class="text-xs text-secondary mt-1">{{ feat.desc }}</p>
            </router-link>
          </div>
        </section>

        <!-- 6. Monitored Domains (Pro only) -->
        <section v-if="isPro && monitors.length > 0" class="mb-10 animate-slide-up" style="animation-delay: 200ms">
          <div class="flex items-center justify-between mb-4">
            <h2 class="font-display text-lg font-bold tracking-tight">Monitored domains</h2>
            <router-link to="/monitoring" class="text-[13px] text-accent hover:text-accent-hover transition-colors font-display font-medium">
              Manage
            </router-link>
          </div>
          <div class="space-y-2">
            <div
              v-for="mon in monitors"
              :key="mon.id"
              class="flex items-center gap-4 px-5 py-3.5 border border-border rounded-lg bg-surface"
            >
              <div class="flex-1 min-w-0">
                <p class="text-sm font-display font-semibold text-primary truncate">{{ mon.domain }}</p>
                <p class="text-xs text-muted">
                  Last score: <span class="font-display font-semibold" :class="scoreColorClass(mon.last_score)">{{ mon.last_score ?? '—' }}</span>
                </p>
              </div>
              <router-link
                :to="{ name: 'History', params: { domain: mon.domain } }"
                class="text-[13px] text-accent hover:text-accent-hover transition-colors font-display font-medium"
              >
                View history
              </router-link>
            </div>
          </div>
        </section>

      </div>
    </div>
  </AppLayout>
</template>
