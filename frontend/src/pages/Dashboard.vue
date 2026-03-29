<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { isLoggedIn, isPro, user, logout } from '../auth.js'
import { getUserScans, getMonitors, createCheckoutSession, createBillingPortal, startScan } from '../api.js'
import ScoreCircle from '../components/ScoreCircle.vue'
import AppLayout from '../components/AppLayout.vue'

const router = useRouter()

const scans = ref([])
const monitors = ref([])
const loadingScans = ref(true)
const loadingMonitors = ref(false)
const error = ref('')
const upgrading = ref(false)
const managingBilling = ref(false)
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

async function handleUpgrade() {
  upgrading.value = true
  try {
    const session = await createCheckoutSession('pro', null)
    const url = session.checkout_url || session.url
    if (url) window.location.href = url
  } catch (e) {
    error.value = e.message || 'Could not start checkout.'
  } finally {
    upgrading.value = false
  }
}

async function handleManageSubscription() {
  managingBilling.value = true
  try {
    const data = await createBillingPortal()
    if (data.portal_url) {
      window.location.href = data.portal_url
    }
  } catch (e) {
    error.value = e.message || 'Could not open billing portal.'
  } finally {
    managingBilling.value = false
  }
}

// Normalize scan data from API
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
      <!-- Header -->
      <div class="border-b border-border-light bg-warm-50">
        <div class="max-w-5xl mx-auto px-6 lg:px-8 py-8 animate-fade-in">
          <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <div class="flex items-center gap-3 mb-1">
                <h1 class="font-display text-xl font-bold tracking-tight text-primary">Dashboard</h1>
                <span
                  class="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-display font-bold uppercase tracking-wider"
                  :class="isPro ? 'bg-accent text-white' : 'bg-warm-200 text-warm-600'"
                >
                  {{ isPro ? 'Pro' : 'Free' }}
                </span>
              </div>
              <p class="text-sm text-secondary">{{ user?.email }}</p>
            </div>
            <div class="flex gap-3">
              <template v-if="isPro">
                <button
                  @click="handleManageSubscription"
                  :disabled="managingBilling"
                  class="btn-secondary text-sm"
                >
                  {{ managingBilling ? 'Loading...' : 'Manage subscription' }}
                </button>
              </template>
              <form @submit.prevent="handleScan" class="flex gap-2">
                <input v-model="scanDomain" type="text" placeholder="Enter domain..." class="input-field text-sm" />
                <button type="submit" class="btn-primary text-sm" :disabled="scanning || !scanDomain.trim()">
                  {{ scanning ? 'Scanning...' : 'Run scan' }}
                </button>
              </form>
              <router-link v-if="isPro" to="/compare" class="btn-secondary text-sm">Compare</router-link>
            </div>
          </div>
          <!-- Pro plan active badge -->
          <div v-if="isPro" class="mt-3 flex items-center gap-2 text-sm text-accent">
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span class="font-display font-medium">Pro plan active</span>
          </div>
        </div>
      </div>

      <div class="max-w-5xl mx-auto px-6 lg:px-8 py-8">

        <!-- Stats row (only if we have scans) -->
        <section v-if="completedScans.length > 0" class="mb-10 animate-slide-up">
          <div class="grid grid-cols-3 gap-6">
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
                <span class="text-sm text-muted font-normal ml-1">{{ bestScan?.domain }}</span>
              </p>
            </div>
          </div>
        </section>

        <!-- Recent scans -->
        <section class="mb-10 animate-slide-up" style="animation-delay: 80ms">
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

          <div v-else-if="error" class="py-8 text-center">
            <p class="text-sm text-score-bad">{{ error }}</p>
          </div>

          <div v-else-if="scans.length === 0" class="border border-dashed border-border rounded-lg p-10 text-center">
            <p class="font-display font-semibold text-primary mb-1">No scans yet</p>
            <p class="text-sm text-secondary mb-4">Run your first scan to see how your site performs.</p>
            <router-link to="/" class="btn-primary">Run a scan</router-link>
          </div>

          <div v-else class="space-y-2">
            <router-link
              v-for="scan in scans"
              :key="scan.scan_id"
              :to="scan.status === 'completed' ? { name: 'Report', params: { id: scan.scan_id } } : { name: 'ScanProgress', params: { id: scan.scan_id } }"
              class="flex items-center gap-5 px-5 py-4 border border-border rounded-lg bg-surface hover:border-warm-300 transition-colors group cursor-pointer"
            >
              <!-- Score circle or status -->
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
                <div class="flex items-center gap-2">
                  <p class="text-sm font-display font-semibold text-primary truncate group-hover:text-accent transition-colors">
                    {{ scan.domain }}
                  </p>
                  <span v-if="scan.status === 'completed' && scan.score != null"
                    class="text-xs font-display font-bold px-1.5 py-0.5 rounded"
                    :class="{
                      'bg-score-good/10 text-score-good': scan.score >= 70,
                      'bg-score-medium/10 text-score-medium': scan.score >= 40 && scan.score < 70,
                      'bg-score-bad/10 text-score-bad': scan.score < 40,
                    }"
                  >
                    {{ scan.grade }}
                  </span>
                  <span v-else-if="scan.status === 'running' || scan.status === 'pending'"
                    class="text-[11px] font-display text-accent bg-accent/10 px-1.5 py-0.5 rounded"
                  >
                    Scanning...
                  </span>
                </div>
                <p class="text-xs text-muted mt-0.5">
                  <span v-if="scan.score != null">Score: {{ scan.score }}/100</span>
                  <span v-if="scan.created_at"> &middot; {{ formatDate(scan.created_at) }}</span>
                </p>
              </div>

              <!-- Arrow -->
              <svg class="w-4 h-4 text-warm-300 group-hover:text-accent transition-colors flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
              </svg>
            </router-link>
          </div>
        </section>

        <!-- Monitored domains (Pro) -->
        <section v-if="isPro && monitors.length > 0" class="mb-10 animate-slide-up" style="animation-delay: 120ms">
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
                class="text-[13px] text-secondary hover:text-primary transition-colors"
              >
                History
              </router-link>
            </div>
          </div>
        </section>

        <!-- Upgrade CTA (Free users) -->
        <section v-if="!isPro" class="mb-10 animate-slide-up" style="animation-delay: 160ms">
          <div class="border border-accent/20 rounded-lg overflow-hidden">
            <div class="bg-accent/[0.04] px-6 py-6 sm:flex sm:items-center sm:justify-between gap-6">
              <div class="mb-4 sm:mb-0">
                <h3 class="font-display font-bold text-primary mb-1">Upgrade to Pro</h3>
                <p class="text-sm text-secondary leading-relaxed max-w-md">
                  Unlock weekly monitoring, competitor comparison, score history, unlimited fix files, and AI bot traffic tracking.
                </p>
                <p class="text-xs text-muted mt-2">$29/month &middot; Cancel anytime</p>
              </div>
              <button
                @click="handleUpgrade"
                :disabled="upgrading"
                class="btn-primary flex-shrink-0 px-6"
              >
                {{ upgrading ? 'Starting...' : 'Upgrade to Pro — $29/mo' }}
              </button>
            </div>
          </div>
        </section>

        <!-- Quick links -->
        <section class="animate-slide-up" style="animation-delay: 200ms">
          <div class="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <router-link to="/compare" class="border border-border rounded-lg p-5 bg-surface hover:border-warm-300 transition-colors group">
              <h4 class="font-display font-semibold text-sm text-primary group-hover:text-accent transition-colors mb-1">Compare competitors</h4>
              <p class="text-xs text-secondary">Side-by-side comparison of up to 4 domains.</p>
              <span v-if="!isPro" class="text-[10px] text-muted font-display uppercase tracking-wider mt-2 inline-block">Pro</span>
            </router-link>
            <router-link to="/monitoring" class="border border-border rounded-lg p-5 bg-surface hover:border-warm-300 transition-colors group">
              <h4 class="font-display font-semibold text-sm text-primary group-hover:text-accent transition-colors mb-1">Monitoring</h4>
              <p class="text-xs text-secondary">Weekly re-scans and score change alerts.</p>
              <span v-if="!isPro" class="text-[10px] text-muted font-display uppercase tracking-wider mt-2 inline-block">Pro</span>
            </router-link>
            <router-link to="/history" class="border border-border rounded-lg p-5 bg-surface hover:border-warm-300 transition-colors group">
              <h4 class="font-display font-semibold text-sm text-primary group-hover:text-accent transition-colors mb-1">Score history</h4>
              <p class="text-xs text-secondary">Track your score improvements over time.</p>
              <span v-if="!isPro" class="text-[10px] text-muted font-display uppercase tracking-wider mt-2 inline-block">Pro</span>
            </router-link>
            <router-link
              :to="completedScans.length > 0 ? { name: 'Report', params: { id: completedScans[0].scan_id }, hash: '#discovery' } : '/'"
              class="border border-border rounded-lg p-5 bg-surface hover:border-warm-300 transition-colors group"
            >
              <h4 class="font-display font-semibold text-sm text-primary group-hover:text-accent transition-colors mb-1">AI Discovery Test</h4>
              <p class="text-xs text-secondary">Check if AI agents actually recommend your store.</p>
              <span class="text-[10px] font-display uppercase tracking-wider mt-2 inline-block" :class="isPro ? 'text-accent' : 'text-muted'">
                {{ completedScans.length > 0 ? 'Run test →' : 'Scan first' }}
              </span>
            </router-link>
          </div>
        </section>
      </div>
    </div>
  </AppLayout>
</template>
