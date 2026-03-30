<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { isLoggedIn, isPro, user, logout } from '../auth.js'
import { getMonitors, addMonitor, removeMonitor, getUserScans } from '../api.js'
import AppLayout from '../components/AppLayout.vue'

const router = useRouter()

const monitors = ref([])
const allScans = ref([])
const newDomain = ref('')
const loading = ref(true)
const adding = ref(false)
const error = ref('')
const addError = ref('')
const showSuggestions = ref(false)

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
  if (score == null) return 'text-muted'
  if (score >= 70) return 'text-score-good'
  if (score >= 40) return 'text-score-medium'
  return 'text-score-bad'
}

function scoreDotClass(score) {
  if (score == null) return 'bg-warm-300'
  if (score >= 70) return 'bg-score-good'
  if (score >= 40) return 'bg-score-medium'
  return 'bg-score-bad'
}

// Status for a monitor: healthy / dropped / issue / pending
function monitorStatus(mon) {
  if (mon.last_score == null) return 'pending'
  if (mon.score_delta != null && mon.score_delta <= -10) return 'dropped'
  if (mon.last_score < 40) return 'issue'
  return 'healthy'
}

function statusDotClass(mon) {
  const s = monitorStatus(mon)
  if (s === 'healthy') return 'bg-score-good'
  if (s === 'dropped') return 'bg-score-medium'
  if (s === 'issue') return 'bg-score-bad'
  return 'bg-warm-300'
}

function statusLabel(mon) {
  const s = monitorStatus(mon)
  if (s === 'healthy') return 'Healthy'
  if (s === 'dropped') return 'Score dropped'
  if (s === 'issue') return 'Needs attention'
  return 'Pending'
}

function statusTextClass(mon) {
  const s = monitorStatus(mon)
  if (s === 'healthy') return 'text-score-good'
  if (s === 'dropped') return 'text-score-medium'
  if (s === 'issue') return 'text-score-bad'
  return 'text-muted'
}

function formatDate(dateStr) {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric',
  })
}

function formatDateShort(dateStr) {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleDateString('en-US', {
    month: 'short', day: 'numeric',
  })
}

// Unique scanned domains not already monitored
const monitoredDomains = computed(() => new Set(monitors.value.map(m => m.domain)))

const scannedDomains = computed(() => {
  const seen = new Set()
  const result = []
  for (const s of allScans.value) {
    if (s.domain && !seen.has(s.domain)) {
      seen.add(s.domain)
      result.push(s)
    }
  }
  return result
})

const unmonitoredScans = computed(() =>
  scannedDomains.value.filter(s => !monitoredDomains.value.has(s.domain))
)

// Filtered suggestions for the input autocomplete
const domainSuggestions = computed(() => {
  const query = newDomain.value.trim().toLowerCase()
  return scannedDomains.value
    .filter(s => !monitoredDomains.value.has(s.domain))
    .filter(s => !query || s.domain.toLowerCase().includes(query))
    .slice(0, 5)
})

// Most recent completed scan per domain for showing scores
const latestScanByDomain = computed(() => {
  const map = {}
  for (const s of allScans.value) {
    if (s.status !== 'completed' || !s.domain) continue
    if (!map[s.domain] || new Date(s.created_at) > new Date(map[s.domain].created_at)) {
      map[s.domain] = s
    }
  }
  return map
})

// Last 4 scores per monitored domain for sparklines (mock from allScans)
const sparklineData = computed(() => {
  const result = {}
  for (const mon of monitors.value) {
    const domainScans = allScans.value
      .filter(s => s.domain === mon.domain && s.status === 'completed' && s.score != null)
      .sort((a, b) => new Date(a.created_at) - new Date(b.created_at))
      .slice(-4)
    result[mon.domain] = domainScans.map(s => s.score)
  }
  return result
})

async function fetchMonitors() {
  try {
    const data = await getMonitors()
    monitors.value = Array.isArray(data) ? data : (data.monitors || [])
  } catch (e) {
    error.value = e.message || 'Could not load monitors.'
  }
}

async function fetchScans() {
  try {
    const data = await getUserScans()
    const raw = Array.isArray(data) ? data : (data.scans || [])
    allScans.value = raw.map(normalizeScan).sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
  } catch {
    // non-critical — suggestions just won't appear
  }
}

async function handleAdd(domainStr) {
  const domain = (domainStr || newDomain.value).trim()
  if (!domain) return

  addError.value = ''
  adding.value = true
  showSuggestions.value = false
  try {
    const mon = await addMonitor(domain)
    monitors.value.push(mon)
    newDomain.value = ''
  } catch (e) {
    addError.value = e.message || 'Could not add domain.'
  } finally {
    adding.value = false
  }
}

async function handleRemove(id) {
  try {
    await removeMonitor(id)
    monitors.value = monitors.value.filter(m => m.id !== id)
  } catch (e) {
    error.value = e.message || 'Could not remove domain.'
  }
}

function selectSuggestion(domain) {
  newDomain.value = domain
  showSuggestions.value = false
}

function handleInputFocus() {
  showSuggestions.value = true
}

function handleInputBlur() {
  // Delay to allow click on suggestion
  setTimeout(() => { showSuggestions.value = false }, 200)
}

// Sparkline: generate SVG polyline points from up to 4 scores
function sparklinePoints(scores) {
  if (!scores || scores.length === 0) return ''
  const w = 52
  const h = 20
  const pts = scores.map((s, i) => {
    const x = scores.length === 1 ? w / 2 : (i / (scores.length - 1)) * w
    const y = h - (s / 100) * h
    return `${x.toFixed(1)},${y.toFixed(1)}`
  })
  return pts.join(' ')
}

function sparklineColor(scores) {
  if (!scores || scores.length < 2) return '#9C9789'
  const last = scores[scores.length - 1]
  const prev = scores[scores.length - 2]
  if (last > prev) return '#3D8B5E'
  if (last < prev) return '#C25544'
  return '#9C9789'
}

onMounted(async () => {
  await Promise.all([fetchMonitors(), fetchScans()])
  loading.value = false
})
</script>

<template>
  <AppLayout>
    <div class="flex-1 pb-16 sm:pb-0">
      <div class="max-w-5xl mx-auto px-6 lg:px-8 py-10">

        <!-- Page header -->
        <div class="animate-fade-in mb-8 pb-6 border-b border-border-light">
          <p class="section-label mb-2">Pro feature</p>
          <div class="flex items-end justify-between gap-4 flex-wrap">
            <div>
              <h1 class="font-display text-2xl font-bold tracking-tight text-primary">Domain monitoring</h1>
              <p class="text-sm text-secondary mt-1.5 max-w-md leading-relaxed">
                Weekly re-scans with alerts when your score changes. We'll catch regressions before your customers do.
              </p>
            </div>
          </div>
        </div>

        <!-- Pro gate -->
        <div v-if="!isPro" class="border-l-4 border-accent rounded-r-lg p-6 bg-accent/[0.03] animate-slide-up">
          <h3 class="font-display font-semibold text-primary mb-1">Monitor your sites 24/7</h3>
          <p class="text-sm text-secondary mb-4 max-w-sm">
            We'll alert you when your score changes. Available on Pro.
          </p>
          <router-link to="/pricing" class="btn-primary">Upgrade to Pro</router-link>
        </div>

        <!-- Monitoring content -->
        <div v-else class="animate-slide-up">

          <!-- Add domain form — pill style -->
          <div class="mb-8">
            <form @submit.prevent="handleAdd()" class="flex gap-3 max-w-lg">
              <div class="relative flex-1">
                <span class="absolute inset-y-0 left-3 flex items-center pointer-events-none">
                  <svg class="w-3.5 h-3.5 text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
                  </svg>
                </span>
                <input
                  v-model="newDomain"
                  type="text"
                  placeholder="domain-to-monitor.com"
                  class="input-field pl-8 text-sm w-full focus:ring-2 focus:ring-accent/40 focus:border-accent"
                  :disabled="adding"
                  @focus="handleInputFocus"
                  @blur="handleInputBlur"
                  @input="showSuggestions = true"
                />
                <!-- Domain suggestions -->
                <div
                  v-if="showSuggestions && domainSuggestions.length > 0"
                  class="absolute z-20 left-0 right-0 top-full mt-1 border border-border rounded-lg bg-surface shadow-lg overflow-hidden"
                >
                  <button
                    v-for="s in domainSuggestions"
                    :key="s.domain"
                    type="button"
                    @mousedown.prevent="selectSuggestion(s.domain)"
                    class="w-full text-left px-3 py-2.5 text-sm hover:bg-warm-50 transition-colors flex items-center justify-between gap-3"
                  >
                    <span class="font-display text-primary truncate text-[13px]">{{ s.domain }}</span>
                    <span v-if="s.score != null" class="flex items-center gap-1.5 shrink-0">
                      <span class="w-1.5 h-1.5 rounded-full shrink-0" :class="scoreDotClass(s.score)"></span>
                      <span class="text-xs font-display font-semibold tabular-nums" :class="scoreColorClass(s.score)">{{ s.score }}</span>
                    </span>
                  </button>
                </div>
              </div>
              <button
                type="submit"
                class="btn-primary whitespace-nowrap"
                :disabled="adding || !newDomain.trim()"
              >
                <svg v-if="adding" class="w-3.5 h-3.5 mr-2 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                {{ adding ? 'Adding...' : 'Add domain' }}
              </button>
            </form>
            <p v-if="addError" class="text-sm text-score-bad mt-2">{{ addError }}</p>
          </div>

          <!-- Loading -->
          <div v-if="loading" class="py-10 flex flex-col items-center gap-2">
            <svg class="w-5 h-5 text-accent animate-spin" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            <p class="text-sm text-muted">Loading monitors...</p>
          </div>

          <div v-else-if="error" class="py-8">
            <p class="text-sm text-score-bad">{{ error }}</p>
          </div>

          <template v-else>

            <!-- Active monitors table -->
            <div v-if="monitors.length > 0" class="mb-8">
              <div class="flex items-center gap-2 mb-3">
                <p class="section-label">Active monitors</p>
                <span class="text-[10px] font-display font-semibold bg-accent/10 text-accent px-1.5 py-0.5 rounded-full tabular-nums">{{ monitors.length }}</span>
              </div>

              <div class="border border-border rounded-lg overflow-hidden bg-surface">
                <!-- Table header -->
                <div class="hidden sm:grid grid-cols-[1fr_80px_56px_120px_120px_auto] gap-0 px-4 py-2.5 border-b border-border-light bg-warm-50">
                  <span class="text-[11px] font-display font-semibold text-muted uppercase tracking-wider">Domain</span>
                  <span class="text-[11px] font-display font-semibold text-muted uppercase tracking-wider text-right">Score</span>
                  <span class="text-[11px] font-display font-semibold text-muted uppercase tracking-wider text-center">Grade</span>
                  <span class="text-[11px] font-display font-semibold text-muted uppercase tracking-wider text-right">Last scan</span>
                  <span class="text-[11px] font-display font-semibold text-muted uppercase tracking-wider">Status</span>
                  <span class="text-[11px] font-display font-semibold text-muted uppercase tracking-wider text-right">Actions</span>
                </div>

                <!-- Rows -->
                <div class="stagger-children">
                  <div
                    v-for="mon in monitors"
                    :key="mon.id"
                    class="grid sm:grid-cols-[1fr_80px_56px_120px_120px_auto] gap-0 px-4 py-3 border-b border-border-light last:border-b-0 items-center transition-colors hover:bg-warm-50"
                  >
                    <!-- Domain + sparkline -->
                    <div class="flex items-center gap-3 min-w-0">
                      <div class="min-w-0">
                        <p class="text-sm font-display font-semibold text-primary truncate">{{ mon.domain }}</p>
                        <!-- Mobile sub-info -->
                        <p class="sm:hidden text-xs text-muted mt-0.5 flex items-center gap-1.5">
                          <span class="w-1.5 h-1.5 rounded-full inline-block" :class="statusDotClass(mon)"></span>
                          <span :class="statusTextClass(mon)">{{ statusLabel(mon) }}</span>
                          <span class="text-warm-300">·</span>
                          <span>{{ formatDateShort(mon.last_scan_at) }}</span>
                        </p>
                      </div>
                      <!-- Mini sparkline SVG -->
                      <div v-if="sparklineData[mon.domain] && sparklineData[mon.domain].length >= 2" class="hidden sm:block shrink-0">
                        <svg width="52" height="20" viewBox="0 0 52 20" fill="none" class="overflow-visible">
                          <polyline
                            :points="sparklinePoints(sparklineData[mon.domain])"
                            :stroke="sparklineColor(sparklineData[mon.domain])"
                            stroke-width="1.5"
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            fill="none"
                          />
                          <!-- End dot -->
                          <circle
                            v-if="sparklineData[mon.domain].length >= 1"
                            :cx="52"
                            :cy="20 - (sparklineData[mon.domain][sparklineData[mon.domain].length - 1] / 100) * 20"
                            r="2"
                            :fill="sparklineColor(sparklineData[mon.domain])"
                          />
                        </svg>
                      </div>
                    </div>

                    <!-- Score -->
                    <div class="hidden sm:flex items-center justify-end gap-1.5">
                      <span class="w-1.5 h-1.5 rounded-full shrink-0" :class="scoreDotClass(mon.last_score)"></span>
                      <span class="text-sm font-display font-semibold tabular-nums" :class="scoreColorClass(mon.last_score)">
                        {{ mon.last_score ?? '—' }}
                      </span>
                    </div>

                    <!-- Grade -->
                    <div class="hidden sm:block text-center">
                      <span class="text-sm font-display font-semibold text-secondary tabular-nums">
                        {{ mon.last_score != null ? gradeFor(mon.last_score) : '—' }}
                      </span>
                    </div>

                    <!-- Last scan -->
                    <div class="hidden sm:block text-right">
                      <span class="text-xs text-muted">{{ formatDate(mon.last_scan_at) }}</span>
                    </div>

                    <!-- Status -->
                    <div class="hidden sm:flex items-center gap-1.5">
                      <span class="w-1.5 h-1.5 rounded-full shrink-0" :class="statusDotClass(mon)"></span>
                      <span class="text-[12px] font-display" :class="statusTextClass(mon)">{{ statusLabel(mon) }}</span>
                    </div>

                    <!-- Actions -->
                    <div class="flex items-center justify-end gap-1">
                      <router-link
                        v-if="mon.last_score != null"
                        :to="{ name: 'History', params: { domain: mon.domain } }"
                        class="btn-ghost text-[12px] px-2 py-1"
                      >
                        History
                      </router-link>
                      <button
                        @click="handleRemove(mon.id)"
                        class="btn-ghost text-[12px] px-2 py-1 text-score-bad hover:text-score-bad hover:bg-red-50"
                        title="Remove monitoring"
                      >
                        <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                          <path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Scanned domains not yet monitored -->
            <div v-if="unmonitoredScans.length > 0">
              <p class="section-label mb-3">{{ monitors.length > 0 ? 'Add from recent scans' : 'Your recent scans' }}</p>

              <div class="border border-border rounded-lg overflow-hidden bg-surface">
                <div class="stagger-children">
                  <div
                    v-for="s in unmonitoredScans"
                    :key="s.scan_id"
                    class="flex items-center gap-4 px-4 py-3 border-b border-border-light last:border-b-0 hover:bg-warm-50 transition-colors"
                  >
                    <div class="flex-1 min-w-0 flex items-center gap-2.5">
                      <span class="w-1.5 h-1.5 rounded-full shrink-0" :class="scoreDotClass(s.score)"></span>
                      <div class="min-w-0">
                        <p class="text-sm font-display font-semibold text-primary truncate">{{ s.domain }}</p>
                        <p class="text-xs text-muted">
                          Score
                          <span v-if="s.score != null" class="font-display font-semibold ml-0.5" :class="scoreColorClass(s.score)">{{ s.score }}</span>
                          <span v-else>—</span>
                          <span class="text-warm-300 mx-1">·</span>
                          {{ formatDateShort(s.created_at) }}
                        </p>
                      </div>
                    </div>
                    <div class="flex items-center gap-2 shrink-0">
                      <router-link
                        v-if="s.scan_id && s.status === 'completed'"
                        :to="{ name: 'Report', params: { id: s.scan_id } }"
                        class="btn-ghost text-[12px] px-2 py-1"
                      >
                        Report
                      </router-link>
                      <button
                        @click="handleAdd(s.domain)"
                        class="btn-primary text-[12px] !py-1.5 !px-3"
                        :disabled="adding"
                      >
                        Monitor
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Fully empty state -->
            <div v-else-if="monitors.length === 0" class="border border-border-light rounded-lg p-10 text-center bg-warm-50">
              <div class="w-10 h-10 rounded-full bg-accent/10 flex items-center justify-center mx-auto mb-3">
                <svg class="w-5 h-5 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                </svg>
              </div>
              <p class="font-display font-semibold text-primary text-sm mb-1">Monitor your sites 24/7</p>
              <p class="text-sm text-secondary mb-4">We'll alert you when your score changes. Run a scan first, then add your domain.</p>
              <router-link to="/" class="btn-primary inline-flex">Run a scan</router-link>
            </div>

          </template>
        </div>
      </div>
    </div>
  </AppLayout>
</template>
