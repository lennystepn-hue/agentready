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

// Chart tooltip state
const tooltip = ref(null) // { x, y, score, date, idx }
const chartRef = ref(null)
const chartAnimated = ref(false)

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

function scoreColor(score) {
  if (score == null) return '#9C9789'
  if (score >= 70) return '#3D8B5E'
  if (score >= 40) return '#C08832'
  return '#C25544'
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric',
  })
}

function formatDateShort(dateStr) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('en-US', {
    month: 'short', day: 'numeric',
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

// Scans for the currently selected domain (newest first)
const history = computed(() => {
  if (!domain.value) return []
  return scansByDomain.value[domain.value] || []
})

// Chronological (oldest first) for the chart
const historyChronological = computed(() => {
  return [...history.value].reverse()
})

// Score delta from previous scan (for table rows — newest first)
const historyWithDelta = computed(() => {
  return history.value.map((entry, idx) => {
    const prev = history.value[idx + 1] // next in array = older scan
    const delta = prev && entry.score != null && prev.score != null
      ? entry.score - prev.score
      : null
    return { ...entry, delta }
  })
})

// Trend indicator: compare most recent vs oldest scan in selection
const trendIndicator = computed(() => {
  const scans = historyChronological.value.filter(s => s.score != null)
  if (scans.length < 2) return null
  const first = scans[0].score
  const last = scans[scans.length - 1].score
  const diff = last - first
  return { diff, abs: Math.abs(diff), up: diff > 0, down: diff < 0 }
})

// SVG area chart geometry
const CHART_W = 600
const CHART_H = 120
const CHART_PAD_X = 12
const CHART_PAD_Y = 12

const chartPoints = computed(() => {
  const scans = historyChronological.value.filter(s => s.score != null)
  if (scans.length === 0) return []
  const n = scans.length
  return scans.map((s, i) => {
    const x = n === 1
      ? CHART_W / 2
      : CHART_PAD_X + (i / (n - 1)) * (CHART_W - CHART_PAD_X * 2)
    const y = CHART_PAD_Y + (1 - s.score / 100) * (CHART_H - CHART_PAD_Y * 2)
    return { x, y, score: s.score, date: s.created_at, idx: i }
  })
})

const chartPolyline = computed(() => {
  return chartPoints.value.map(p => `${p.x.toFixed(2)},${p.y.toFixed(2)}`).join(' ')
})

// Closed path for area fill (polyline + bottom corners)
const chartAreaPath = computed(() => {
  const pts = chartPoints.value
  if (pts.length === 0) return ''
  const line = pts.map(p => `${p.x.toFixed(2)},${p.y.toFixed(2)}`).join(' L ')
  const firstX = pts[0].x.toFixed(2)
  const lastX = pts[pts.length - 1].x.toFixed(2)
  const bottom = (CHART_H - CHART_PAD_Y + 4).toFixed(2)
  return `M ${firstX},${bottom} L ${line} L ${lastX},${bottom} Z`
})

// Dominant color for chart (based on last score)
const chartColor = computed(() => {
  const scans = historyChronological.value.filter(s => s.score != null)
  if (scans.length === 0) return '#0D7377'
  return scoreColor(scans[scans.length - 1].score)
})

function selectDomain(d) {
  domain.value = d
  router.replace({ name: 'History', params: { domain: d } })
  chartAnimated.value = false
  tooltip.value = null
  setTimeout(() => { chartAnimated.value = true }, 80)
}

function handleChartMouseMove(e) {
  const pts = chartPoints.value
  if (pts.length === 0) return
  const rect = e.currentTarget.getBoundingClientRect()
  const mouseX = ((e.clientX - rect.left) / rect.width) * CHART_W
  // Find nearest point
  let nearest = pts[0]
  let minDist = Math.abs(pts[0].x - mouseX)
  for (const p of pts) {
    const d = Math.abs(p.x - mouseX)
    if (d < minDist) { minDist = d; nearest = p }
  }
  tooltip.value = {
    x: nearest.x,
    y: nearest.y,
    score: nearest.score,
    date: nearest.date,
    idx: nearest.idx,
  }
}

function handleChartMouseLeave() {
  tooltip.value = null
}

onMounted(async () => {
  try {
    const data = await getUserScans()
    const raw = Array.isArray(data) ? data : (data.scans || [])
    allScans.value = raw.map(normalizeScan)

    if (!domain.value && domains.value.length > 0) {
      domain.value = domains.value[0]
      router.replace({ name: 'History', params: { domain: domains.value[0] } })
    }
  } catch (e) {
    error.value = e.message || 'Could not load scans.'
  } finally {
    loading.value = false
    setTimeout(() => { chartAnimated.value = true }, 120)
  }
})

watch(domain, () => {
  chartAnimated.value = false
  tooltip.value = null
  setTimeout(() => { chartAnimated.value = true }, 80)
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
              <h1 class="font-display text-2xl font-bold tracking-tight text-primary">Score history</h1>
              <p class="text-sm text-secondary mt-1.5 max-w-md leading-relaxed">
                Track how your AI agent readiness score changes over time across all your domains.
              </p>
            </div>
            <!-- Trend badge — shown when we have data -->
            <div
              v-if="isPro && trendIndicator && !loading"
              class="shrink-0 flex items-center gap-1.5 px-3 py-1.5 rounded-full border text-sm font-display font-semibold tabular-nums"
              :class="trendIndicator.up
                ? 'border-score-good/30 bg-score-good/[0.06] text-score-good'
                : trendIndicator.down
                  ? 'border-score-bad/30 bg-score-bad/[0.06] text-score-bad'
                  : 'border-border text-muted'"
            >
              <span v-if="trendIndicator.up" aria-hidden="true">&#8593;</span>
              <span v-else-if="trendIndicator.down" aria-hidden="true">&#8595;</span>
              <span v-else aria-hidden="true">&#8212;</span>
              <span>
                {{ trendIndicator.up ? '+' : trendIndicator.down ? '-' : '' }}{{ trendIndicator.abs }} pts this period
              </span>
            </div>
          </div>
        </div>

        <!-- Pro gate -->
        <div v-if="!isPro" class="border-l-4 border-accent rounded-r-lg p-6 bg-accent/[0.03] animate-slide-up">
          <h3 class="font-display font-semibold text-primary mb-1">Track your progress over time</h3>
          <p class="text-sm text-secondary mb-4 max-w-sm">
            Score history lets you see how your AI readiness improves scan by scan. Available on Pro.
          </p>
          <router-link to="/pricing" class="btn-primary">Upgrade to Pro</router-link>
        </div>

        <!-- History content -->
        <div v-else class="animate-slide-up">

          <!-- Loading -->
          <div v-if="loading" class="py-12 flex flex-col items-center gap-3">
            <svg class="w-5 h-5 text-accent animate-spin" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            <p class="text-sm text-muted">Loading history...</p>
          </div>

          <div v-else-if="error" class="py-8 text-center">
            <p class="text-sm text-score-bad">{{ error }}</p>
          </div>

          <!-- No scans at all -->
          <div v-else-if="allScans.length === 0" class="border border-border-light rounded-lg p-10 text-center bg-warm-50">
            <div class="w-10 h-10 rounded-full bg-accent/10 flex items-center justify-center mx-auto mb-3">
              <svg class="w-5 h-5 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <p class="font-display font-semibold text-primary text-sm mb-1">No scan history yet</p>
            <p class="text-sm text-secondary mb-4">Run a scan to start tracking your score over time.</p>
            <router-link to="/" class="btn-primary inline-flex">Run a scan</router-link>
          </div>

          <!-- Has scans -->
          <div v-else>

            <!-- Domain chip selector -->
            <div class="mb-7">
              <p class="section-label mb-3">Domain</p>
              <div class="flex flex-wrap gap-2">
                <button
                  v-for="d in domains"
                  :key="d"
                  @click="selectDomain(d)"
                  class="domain-chip"
                  :class="d === domain ? 'domain-chip--active' : 'domain-chip--inactive'"
                >
                  <span
                    class="w-1.5 h-1.5 rounded-full shrink-0"
                    :class="scansByDomain[d]?.[0]?.score != null ? scoreDotClass(scansByDomain[d][0].score) : 'bg-warm-300'"
                  ></span>
                  {{ d }}
                </button>
              </div>
            </div>

            <!-- Empty history for this domain -->
            <div v-if="history.length === 0" class="border border-border-light rounded-lg p-8 text-center">
              <p class="text-sm text-secondary">No history data for <span class="font-display font-semibold text-primary">{{ domain }}</span> yet.</p>
            </div>

            <!-- Chart + table -->
            <div v-else>

              <!-- SVG Area chart -->
              <div class="mb-8 border border-border rounded-lg bg-surface overflow-hidden">
                <div class="px-5 py-3.5 border-b border-border-light bg-warm-50 flex items-center justify-between">
                  <p class="section-label">Score over time — {{ domain }}</p>
                  <span v-if="historyChronological.length > 0" class="text-xs text-muted font-display">
                    {{ historyChronological.length }} scan{{ historyChronological.length === 1 ? '' : 's' }}
                  </span>
                </div>

                <!-- Chart container -->
                <div
                  class="relative px-2 pt-4 pb-6 select-none"
                  @mousemove="handleChartMouseMove"
                  @mouseleave="handleChartMouseLeave"
                  ref="chartRef"
                >
                  <svg
                    :viewBox="`0 0 ${CHART_W} ${CHART_H}`"
                    class="w-full overflow-visible"
                    :style="{ height: '120px' }"
                    aria-hidden="true"
                  >
                    <defs>
                      <linearGradient id="chart-area-gradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" :stop-color="chartColor" stop-opacity="0.18" />
                        <stop offset="100%" :stop-color="chartColor" stop-opacity="0.01" />
                      </linearGradient>
                      <!-- Clip path for animated reveal -->
                      <clipPath id="chart-reveal-clip">
                        <rect
                          x="0" y="0"
                          :width="chartAnimated ? CHART_W : 0"
                          :height="CHART_H + 20"
                          class="chart-clip-rect"
                        />
                      </clipPath>
                    </defs>

                    <!-- Horizontal guide lines at 25 / 50 / 75 -->
                    <line
                      v-for="pct in [25, 50, 75]"
                      :key="pct"
                      :x1="CHART_PAD_X"
                      :y1="CHART_PAD_Y + (1 - pct / 100) * (CHART_H - CHART_PAD_Y * 2)"
                      :x2="CHART_W - CHART_PAD_X"
                      :y2="CHART_PAD_Y + (1 - pct / 100) * (CHART_H - CHART_PAD_Y * 2)"
                      stroke="#E0DDD7"
                      stroke-width="1"
                      stroke-dasharray="3 4"
                    />

                    <!-- Area fill -->
                    <path
                      v-if="chartAreaPath"
                      :d="chartAreaPath"
                      fill="url(#chart-area-gradient)"
                      clip-path="url(#chart-reveal-clip)"
                    />

                    <!-- Line -->
                    <polyline
                      v-if="chartPolyline"
                      :points="chartPolyline"
                      :stroke="chartColor"
                      stroke-width="2"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      fill="none"
                      clip-path="url(#chart-reveal-clip)"
                    />

                    <!-- Data point dots -->
                    <g clip-path="url(#chart-reveal-clip)">
                      <circle
                        v-for="(pt, i) in chartPoints"
                        :key="i"
                        :cx="pt.x"
                        :cy="pt.y"
                        :r="tooltip && tooltip.idx === i ? 5 : 3"
                        :fill="chartColor"
                        :fill-opacity="tooltip && tooltip.idx === i ? 1 : 0.7"
                        class="chart-dot"
                        :style="{ animationDelay: `${i * 60 + 400}ms` }"
                      />
                    </g>

                    <!-- Tooltip crosshair vertical line -->
                    <line
                      v-if="tooltip"
                      :x1="tooltip.x"
                      :y1="CHART_PAD_Y"
                      :x2="tooltip.x"
                      :y2="CHART_H - CHART_PAD_Y + 4"
                      :stroke="chartColor"
                      stroke-width="1"
                      stroke-dasharray="3 3"
                      stroke-opacity="0.5"
                    />

                    <!-- Y-axis labels -->
                    <text
                      v-for="pct in [25, 50, 75, 100]"
                      :key="'y' + pct"
                      :x="2"
                      :y="CHART_PAD_Y + (1 - pct / 100) * (CHART_H - CHART_PAD_Y * 2) + 3"
                      font-size="8"
                      fill="#9C9789"
                      font-family="'Instrument Sans', system-ui, sans-serif"
                    >{{ pct }}</text>
                  </svg>

                  <!-- Floating tooltip -->
                  <transition name="tooltip-fade">
                    <div
                      v-if="tooltip"
                      class="absolute pointer-events-none z-10 bg-surface border border-border rounded-lg px-3 py-2 shadow-md text-xs font-display"
                      :style="{
                        left: `${Math.min(Math.max(tooltip.x / CHART_W * 100, 8), 78)}%`,
                        top: '4px',
                        transform: 'translateX(-50%)',
                      }"
                    >
                      <div class="font-bold tabular-nums" :class="scoreColorClass(tooltip.score)">{{ tooltip.score }}</div>
                      <div class="text-muted text-[10px] mt-0.5">{{ formatDate(tooltip.date) }}</div>
                    </div>
                  </transition>

                  <!-- X-axis date labels -->
                  <div class="flex justify-between px-3 mt-2">
                    <span class="text-[10px] text-muted font-display">
                      {{ historyChronological.length > 0 ? formatDateShort(historyChronological[0]?.created_at) : '' }}
                    </span>
                    <span v-if="historyChronological.length > 2" class="text-[10px] text-muted font-display">
                      {{ formatDateShort(historyChronological[Math.floor(historyChronological.length / 2)]?.created_at) }}
                    </span>
                    <span class="text-[10px] text-muted font-display">
                      {{ historyChronological.length > 1 ? formatDateShort(historyChronological[historyChronological.length - 1]?.created_at) : '' }}
                    </span>
                  </div>
                </div>
              </div>

              <!-- Scan history table -->
              <div class="border border-border rounded-lg overflow-hidden bg-surface">
                <!-- Table header -->
                <div class="grid grid-cols-[1fr_72px_52px_64px_auto] gap-0 px-5 py-2.5 border-b border-border-light bg-warm-50">
                  <span class="text-[11px] font-display font-semibold text-muted uppercase tracking-wider">Date</span>
                  <span class="text-[11px] font-display font-semibold text-muted uppercase tracking-wider text-right">Score</span>
                  <span class="text-[11px] font-display font-semibold text-muted uppercase tracking-wider text-center">Grade</span>
                  <span class="text-[11px] font-display font-semibold text-muted uppercase tracking-wider text-center">Change</span>
                  <span class="text-[11px] font-display font-semibold text-muted uppercase tracking-wider text-right"></span>
                </div>

                <!-- Rows -->
                <div class="stagger-children">
                  <div
                    v-for="entry in historyWithDelta"
                    :key="entry.scan_id"
                    class="grid grid-cols-[1fr_72px_52px_64px_auto] gap-0 px-5 py-3 border-b border-border-light last:border-b-0 items-center transition-colors hover:bg-warm-50"
                  >
                    <!-- Date -->
                    <div>
                      <span class="text-sm text-secondary font-body">{{ formatDate(entry.created_at) }}</span>
                      <span
                        v-if="entry.status && entry.status !== 'completed'"
                        class="ml-2 text-[10px] font-display font-semibold uppercase tracking-wide text-muted"
                      >{{ entry.status }}</span>
                    </div>

                    <!-- Score -->
                    <div class="text-right flex items-center justify-end gap-1.5">
                      <span class="w-1.5 h-1.5 rounded-full shrink-0" :class="scoreDotClass(entry.score)"></span>
                      <span
                        class="font-display font-bold tabular-nums text-sm"
                        :class="scoreColorClass(entry.score)"
                      >{{ entry.score ?? '—' }}</span>
                    </div>

                    <!-- Grade -->
                    <div class="text-center">
                      <span class="text-sm font-display font-semibold text-secondary tabular-nums">{{ entry.grade }}</span>
                    </div>

                    <!-- Delta arrow -->
                    <div class="text-center">
                      <span
                        v-if="entry.delta !== null && entry.delta !== 0"
                        class="inline-flex items-center gap-0.5 text-[11px] font-display font-semibold tabular-nums px-1.5 py-0.5 rounded"
                        :class="entry.delta > 0
                          ? 'text-score-good bg-score-good/[0.08]'
                          : 'text-score-bad bg-score-bad/[0.08]'"
                      >
                        <span aria-hidden="true">{{ entry.delta > 0 ? '↑' : '↓' }}</span>
                        {{ Math.abs(entry.delta) }}
                      </span>
                      <span
                        v-else-if="entry.delta === 0"
                        class="text-[11px] font-display text-muted"
                        aria-label="No change"
                      >—</span>
                      <span v-else class="text-[11px] text-muted">—</span>
                    </div>

                    <!-- Action -->
                    <div class="text-right">
                      <router-link
                        v-if="entry.scan_id && entry.status === 'completed'"
                        :to="{ name: 'Report', params: { id: entry.scan_id } }"
                        class="text-[12px] text-accent hover:text-accent-hover transition-colors font-display font-medium"
                      >
                        Report
                      </router-link>
                    </div>
                  </div>
                </div>
              </div>

            </div>
          </div>
        </div>

      </div>
    </div>
  </AppLayout>
</template>

<style scoped>
/* Domain chip pill buttons */
.domain-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 12px;
  font-family: 'Instrument Sans', system-ui, sans-serif;
  font-size: 13px;
  font-weight: 500;
  border-radius: 999px;
  border-width: 1px;
  border-style: solid;
  transition: all 150ms ease;
  cursor: pointer;
  white-space: nowrap;
}

.domain-chip--active {
  border-color: #0D7377;
  background-color: #E8F4F4;
  color: #0D7377;
  font-weight: 600;
}

.domain-chip--inactive {
  border-color: #E0DDD7;
  background-color: transparent;
  color: #6B6860;
}

.domain-chip--inactive:hover {
  background-color: #F3F1ED;
  border-color: #D4D0C8;
  color: #1A1917;
}

/* Chart reveal clip path animation */
.chart-clip-rect {
  transition: width 900ms cubic-bezier(0.25, 0.46, 0.45, 0.94);
}

/* Data point dots — scale in with stagger */
.chart-dot {
  opacity: 0;
  transform-origin: center;
  animation: dotScaleIn 300ms cubic-bezier(0.34, 1.2, 0.64, 1) forwards;
}

@keyframes dotScaleIn {
  from {
    opacity: 0;
    r: 0;
  }
  to {
    opacity: 0.85;
    r: 3;
  }
}

/* Tooltip transition */
.tooltip-fade-enter-active,
.tooltip-fade-leave-active {
  transition: opacity 100ms ease, transform 100ms ease;
}

.tooltip-fade-enter-from,
.tooltip-fade-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(-3px);
}
</style>
