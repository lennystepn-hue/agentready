<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { isLoggedIn, isPro, user } from '../auth.js'
import ScoreCircle from '../components/ScoreCircle.vue'
import MentionChart from '../components/MentionChart.vue'
import StepFlow from '../components/StepFlow.vue'
import UpgradeCard from '../components/UpgradeCard.vue'
import AppLayout from '../components/AppLayout.vue'
import {
  getUserScans, getMonitors, startScan, deleteScan,
  getHostedFiles, activateHostedFiles,
  pingCrawlers, getPingHistory,
  getMentions, trackMentions, getCompetitors, discoverCompetitors,
  optimizeContent, simulateAgent,
} from '../api.js'

const router = useRouter()

const scans = ref([])
const loadingScans = ref(true)
const error = ref('')
const scanDomain = ref('')
const scanning = ref(false)

// Pro feature data
const hostedFiles = ref([])
const pingHistory = ref([])
const mentions = ref([])
const competitors = ref([])
const contentSuggs = ref(null)
const simulation = ref(null)
const monitors = ref([])

// Loading/action states
const activatingFiles = ref(false)
const pinging = ref(false)
const discoveringComps = ref(false)
const optimizing = ref(false)
const simulating = ref(false)
const trackingMentions = ref(false)

// UI state
const suggestionsExpanded = ref(false)
const copiedUrl = ref('')

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

function formatTime(dateStr) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleTimeString('en-US', {
    hour: 'numeric', minute: '2-digit',
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

const latestCompletedScan = computed(() => {
  if (completedScans.value.length === 0) return null
  return completedScans.value[0]
})

const primaryDomain = computed(() => latestCompletedScan.value?.domain || '')

const recentScans = computed(() => scans.value.slice(0, 10))

const filesActive = computed(() =>
  hostedFiles.value.length > 0 && hostedFiles.value.some(f => f.is_active || f.public_token)
)

const latestMention = computed(() => {
  if (!mentions.value || mentions.value.length === 0) return null
  return mentions.value[0]
})

const mentionFoundCount = computed(() => {
  if (!latestMention.value) return 0
  return latestMention.value.queries_found || 0
})

const mentionTestedCount = computed(() => {
  if (!latestMention.value) return 0
  return latestMention.value.queries_tested || 0
})

const mentionTrend = computed(() => {
  if (mentions.value.length < 2) return 0
  const curr = mentions.value[0]?.queries_found || 0
  const prev = mentions.value[1]?.queries_found || 0
  return curr - prev
})

const lastPing = computed(() => {
  if (pingHistory.value.length === 0) return null
  return pingHistory.value[0]
})

const recentPings = computed(() => pingHistory.value.slice(0, 3))

const pingsRemaining = computed(() => {
  const today = new Date().toISOString().slice(0, 10)
  const todayPings = pingHistory.value.filter(p =>
    (p.created_at || p.pinged_at || '').startsWith(today)
  ).length
  return Math.max(0, 3 - todayPings)
})

const shownCompetitors = computed(() => competitors.value.slice(0, 5))

const scoreMessage = computed(() => {
  const s = bestScan.value?.score
  if (s == null) return ''
  if (s >= 90) return 'Excellent. AI agents can find and recommend your site with ease.'
  if (s >= 70) return 'Strong visibility. A few tweaks could push you to the top tier.'
  if (s >= 50) return 'Moderate visibility. There are clear opportunities to improve.'
  if (s >= 30) return 'Low visibility. AI agents are struggling to understand your site.'
  return 'Critical. Your site is nearly invisible to AI agents.'
})

const siteTypeLabel = computed(() => {
  const t = latestCompletedScan.value?.site_type
  if (!t) return null
  return t.charAt(0).toUpperCase() + t.slice(1)
})

const suggestionCount = computed(() => contentSuggs.value?.suggestions?.length || 0)

const simulationRate = computed(() => {
  if (!simulation.value?.steps) return 0
  const steps = simulation.value.steps
  const passed = steps.filter(s => s.status === 'pass').length
  return steps.length > 0 ? Math.round((passed / steps.length) * 100) : 0
})

// ---- Actions ----

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

async function handleActivateFiles() {
  if (!primaryDomain.value || !latestCompletedScan.value) return
  activatingFiles.value = true
  try {
    await activateHostedFiles(primaryDomain.value, latestCompletedScan.value.scan_id)
    // Re-fetch to get the full file objects with public_token etc
    const data = await getHostedFiles()
    hostedFiles.value = Array.isArray(data) ? data : (data.files || [])
  } catch (e) {
    error.value = e.message || 'Could not activate files.'
  } finally {
    activatingFiles.value = false
  }
}

async function handlePing() {
  pinging.value = true
  try {
    await pingCrawlers()
    const data = await getPingHistory()
    pingHistory.value = Array.isArray(data) ? data : (data.pings || data.history || [])
  } catch (e) {
    error.value = e.message || 'Ping failed.'
  } finally {
    pinging.value = false
  }
}

async function handleDiscoverCompetitors() {
  if (!primaryDomain.value) return
  discoveringComps.value = true
  try {
    await discoverCompetitors(primaryDomain.value)
    // Re-fetch to get the saved competitor objects
    const data = await getCompetitors(primaryDomain.value)
    competitors.value = Array.isArray(data) ? data : (data.competitors || [])
  } catch (e) {
    error.value = e.message || 'Could not discover competitors.'
  } finally {
    discoveringComps.value = false
  }
}

async function handleOptimize() {
  if (!latestCompletedScan.value) return
  optimizing.value = true
  try {
    const data = await optimizeContent(latestCompletedScan.value.scan_id)
    contentSuggs.value = data
  } catch (e) {
    error.value = e.message || 'Could not generate suggestions.'
  } finally {
    optimizing.value = false
  }
}

async function handleSimulate() {
  if (!latestCompletedScan.value) return
  simulating.value = true
  try {
    const data = await simulateAgent(latestCompletedScan.value.scan_id)
    simulation.value = data
  } catch (e) {
    error.value = e.message || 'Simulation failed.'
  } finally {
    simulating.value = false
  }
}

async function handleTrackMentions() {
  if (!primaryDomain.value) return
  trackingMentions.value = true
  try {
    await trackMentions(primaryDomain.value)
    const data = await getMentions(primaryDomain.value)
    mentions.value = Array.isArray(data) ? data : (data.history || data.mentions || [])
  } catch (e) {
    error.value = e.message || 'Could not track mentions.'
  } finally {
    trackingMentions.value = false
  }
}

const siteOrigin = typeof window !== 'undefined' ? window.location.origin : 'https://agentcheck.site'

function hostedUrl(file) {
  return `${siteOrigin}/hosted/${file.public_token}/${file.file_type}`
}

function copyToClipboard(text) {
  navigator.clipboard.writeText(text)
  copiedUrl.value = text
  setTimeout(() => { copiedUrl.value = '' }, 2000)
}

async function handleDeleteScan(scanId) {
  if (!confirm('Delete this scan? This cannot be undone.')) return
  try {
    await deleteScan(scanId)
    scans.value = scans.value.filter(s => s.scan_id !== scanId)
  } catch (e) {
    error.value = e.message || 'Could not delete scan.'
  }
}

// ---- Data Loading ----

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

  if (isPro.value && primaryDomain.value) {
    const domain = primaryDomain.value
    const scanId = latestCompletedScan.value?.scan_id

    const loads = [
      getHostedFiles().then(d => {
        hostedFiles.value = Array.isArray(d) ? d : (d.files || [])
      }).catch(() => {}),

      getPingHistory().then(d => {
        pingHistory.value = Array.isArray(d) ? d : (d.pings || d.history || [])
      }).catch(() => {}),

      getMentions(domain).then(d => {
        mentions.value = Array.isArray(d) ? d : (d.history || d.mentions || [])
      }).catch(() => {}),

      getCompetitors(domain).then(d => {
        competitors.value = Array.isArray(d) ? d : (d.competitors || [])
      }).catch(() => {}),

      getMonitors().then(d => {
        monitors.value = Array.isArray(d) ? d : (d.monitors || [])
      }).catch(() => {}),
    ]

    await Promise.allSettled(loads)
  } else if (isPro.value) {
    // Pro but no scans yet, still load monitors
    getMonitors().then(d => {
      monitors.value = Array.isArray(d) ? d : (d.monitors || [])
    }).catch(() => {})
  }
})
</script>

<template>
  <AppLayout>
    <div class="flex-1 bg-page">
      <div class="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-10">

        <!-- ============================================================ -->
        <!-- SCAN BAR                                                      -->
        <!-- ============================================================ -->
        <section class="mb-10 animate-fade-in">
          <div class="relative">
            <!-- Ambient glow behind the bar when active -->
            <div
              class="absolute -inset-px rounded-xl transition-opacity duration-500 pointer-events-none"
              :class="scanDomain.trim() ? 'opacity-100' : 'opacity-0'"
              style="background: radial-gradient(ellipse at 50% 100%, rgba(13,115,119,0.12) 0%, transparent 70%); filter: blur(1px);"
            />

            <form
              @submit.prevent="handleScan"
              class="relative flex items-stretch gap-0 rounded-xl border bg-surface shadow-sm transition-all duration-200"
              :class="scanDomain.trim() ? 'border-accent/40 shadow-accent/8' : 'border-border'"
            >
              <!-- Globe icon -->
              <div class="pointer-events-none flex items-center pl-4 pr-2 shrink-0">
                <svg class="w-4 h-4 transition-colors duration-200" :class="scanDomain.trim() ? 'text-accent' : 'text-warm-400'" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.75">
                  <circle cx="12" cy="12" r="10" /><path stroke-linecap="round" stroke-linejoin="round" d="M2 12h20M12 2a15.3 15.3 0 014 10 15.3 15.3 0 01-4 10 15.3 15.3 0 01-4-10 15.3 15.3 0 014-10z" />
                </svg>
              </div>

              <input
                v-model="scanDomain"
                type="text"
                placeholder="Enter a domain to scan — e.g. stripe.com"
                autocomplete="off"
                spellcheck="false"
                class="flex-1 min-w-0 bg-transparent py-4 pr-3 text-sm text-primary placeholder:text-warm-400 focus:outline-none font-body"
              />

              <!-- Keyboard hint — hidden on mobile -->
              <div class="hidden sm:flex items-center pr-3 shrink-0">
                <kbd class="inline-flex items-center gap-1 rounded border border-border-light px-1.5 py-0.5 text-[10px] font-mono text-warm-400 bg-warm-50 leading-none select-none">
                  ↵ Enter
                </kbd>
              </div>

              <!-- Divider -->
              <div class="w-px bg-border self-stretch my-2 shrink-0" />

              <!-- Submit button — pulses when input has content -->
              <button
                type="submit"
                :disabled="scanning || !scanDomain.trim()"
                class="relative flex items-center gap-2 px-5 sm:px-7 py-4 text-sm font-display font-semibold rounded-r-xl transition-all duration-200 shrink-0 disabled:opacity-50 disabled:cursor-not-allowed"
                :class="scanDomain.trim() && !scanning ? 'bg-accent text-white hover:bg-accent-hover' : 'bg-warm-100 text-warm-500'"
              >
                <!-- Pulse ring when ready -->
                <span
                  v-if="scanDomain.trim() && !scanning"
                  class="absolute inset-0 rounded-r-xl animate-ping opacity-20 bg-accent pointer-events-none"
                  style="animation-duration: 2s;"
                />

                <svg v-if="scanning" class="w-4 h-4 animate-spin shrink-0" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                <svg v-else class="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                <span class="hidden sm:inline">{{ scanning ? 'Scanning...' : 'Scan' }}</span>
              </button>
            </form>

            <!-- Quick suggestions row -->
            <div v-if="!scanDomain.trim() && !loadingScans && scans.length === 0" class="flex items-center gap-2 mt-3 flex-wrap">
              <span class="text-xs text-warm-400 font-body">Try:</span>
              <button
                v-for="example in ['stripe.com', 'notion.so', 'linear.app']"
                :key="example"
                type="button"
                @click="scanDomain = example"
                class="text-xs font-body text-secondary hover:text-accent border border-border-light hover:border-accent/30 bg-surface hover:bg-accent/5 px-2.5 py-1 rounded-md transition-all duration-150"
              >
                {{ example }}
              </button>
            </div>
          </div>
          <p v-if="error" class="text-sm text-score-bad mt-3 pl-1">{{ error }}</p>
        </section>

        <!-- ============================================================ -->
        <!-- LOADING STATE — shimmer skeletons                            -->
        <!-- ============================================================ -->
        <div v-if="loadingScans" class="space-y-5">
          <!-- Hero skeleton -->
          <div class="border border-border rounded-xl p-6 sm:p-8 bg-surface animate-pulse">
            <div class="flex items-center gap-6 sm:gap-8">
              <!-- Score circle skeleton -->
              <div class="shrink-0 w-24 h-24 sm:w-36 sm:h-36 rounded-full bg-warm-100" />
              <div class="flex-1 space-y-3">
                <div class="h-2.5 w-24 rounded-full bg-warm-100" />
                <div class="h-10 w-32 rounded-lg bg-warm-200" />
                <div class="flex gap-2 mt-1">
                  <div class="h-6 w-16 rounded-lg bg-warm-100" />
                  <div class="h-6 w-28 rounded-lg bg-warm-100" />
                </div>
                <div class="h-4 w-64 rounded-full bg-warm-100" />
              </div>
            </div>
          </div>

          <!-- Scan history skeleton rows -->
          <div class="border border-border rounded-xl bg-surface overflow-hidden divide-y divide-border-light">
            <div
              v-for="i in 4"
              :key="i"
              class="flex items-center gap-4 px-5 py-4 animate-pulse"
            >
              <!-- Score dot skeleton -->
              <div class="shrink-0 w-8 h-8 rounded-full bg-warm-200" />
              <!-- Domain + date skeleton -->
              <div class="flex-1 space-y-2">
                <div class="h-3.5 rounded-full bg-warm-200" :style="`width: ${55 + (i * 11) % 30}%`" />
                <div class="h-2.5 w-20 rounded-full bg-warm-100" />
              </div>
              <!-- Grade badge skeleton -->
              <div class="shrink-0 h-6 w-10 rounded-lg bg-warm-100" />
              <!-- Arrow skeleton -->
              <div class="shrink-0 h-4 w-4 rounded bg-warm-100" />
            </div>
          </div>
        </div>

        <template v-else>

          <!-- ============================================================ -->
          <!-- HERO SECTION                                                 -->
          <!-- ============================================================ -->

          <!-- ── HAS SCANS ── -->
          <template v-if="completedScans.length > 0">

            <!-- STATUS STRIP — Bloomberg-dense ticker, no card container -->
            <div class="animate-fade-in mb-7">
              <div class="flex flex-wrap items-center gap-y-2 pb-3.5 border-b border-border-light">

                <!-- Score + grade -->
                <div class="flex items-center gap-1.5 pr-4 mr-1 border-r border-border-light">
                  <span
                    class="w-1.5 h-1.5 rounded-full shrink-0"
                    :class="{
                      'bg-score-good': bestScan.score >= 70,
                      'bg-score-medium': bestScan.score >= 40 && bestScan.score < 70,
                      'bg-score-bad': bestScan.score < 40,
                    }"
                  ></span>
                  <span
                    class="font-display text-sm font-bold tabular-nums leading-none"
                    :class="scoreColorClass(bestScan.score)"
                  >{{ bestScan.score }}</span>
                  <span class="font-display text-[10px] font-semibold text-muted uppercase tracking-wider">/100</span>
                  <span
                    class="font-display text-[10px] font-bold px-1.5 py-px rounded ml-0.5"
                    :class="{
                      'bg-score-good/10 text-score-good': bestScan.score >= 70,
                      'bg-score-medium/10 text-score-medium': bestScan.score >= 40 && bestScan.score < 70,
                      'bg-score-bad/10 text-score-bad': bestScan.score < 40,
                    }"
                  >{{ bestScan.grade }}</span>
                </div>

                <!-- Domain + site type -->
                <div v-if="primaryDomain" class="flex items-center gap-1.5 px-4 mr-1 border-r border-border-light">
                  <svg class="w-3 h-3 text-muted shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"/>
                    <path stroke-linecap="round" stroke-linejoin="round" d="M2 12h20M12 2a15.3 15.3 0 010 20M12 2a15.3 15.3 0 000 20"/>
                  </svg>
                  <span class="font-body text-xs text-secondary truncate max-w-[160px]">{{ primaryDomain }}</span>
                  <span v-if="siteTypeLabel" class="font-display text-[10px] uppercase tracking-wider text-warm-500 bg-warm-100 px-1.5 py-px rounded">{{ siteTypeLabel }}</span>
                </div>

                <!-- Mentions (Pro only) -->
                <div v-if="isPro" class="flex items-center gap-1.5 px-4 mr-1 border-r border-border-light">
                  <svg class="w-3 h-3 text-muted shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z"/>
                  </svg>
                  <span class="font-display text-xs tabular-nums text-primary font-bold">{{ mentionFoundCount }}<span class="text-muted font-normal">/{{ mentionTestedCount }}</span></span>
                  <span class="font-display text-[10px] text-muted uppercase tracking-wider">mentions</span>
                  <span v-if="mentionTrend > 0" class="font-display text-[10px] font-bold text-score-good">+{{ mentionTrend }}</span>
                  <span v-else-if="mentionTrend < 0" class="font-display text-[10px] font-bold text-score-bad">{{ mentionTrend }}</span>
                </div>

                <!-- Files status -->
                <div class="flex items-center gap-1.5 px-4 mr-1 border-r border-border-light">
                  <span
                    class="w-1.5 h-1.5 rounded-full shrink-0"
                    :class="filesActive ? 'bg-score-good' : 'bg-warm-300'"
                  ></span>
                  <span class="font-display text-[10px] text-muted uppercase tracking-wider">{{ filesActive ? 'Files live' : 'Files off' }}</span>
                </div>

                <!-- Monitors -->
                <div class="flex items-center gap-1.5 px-4">
                  <span
                    class="w-1.5 h-1.5 rounded-full shrink-0"
                    :class="monitors.length > 0 ? 'bg-score-good animate-pulse-subtle' : 'bg-warm-300'"
                  ></span>
                  <span class="font-display text-[10px] text-muted uppercase tracking-wider">
                    {{ monitors.length > 0 ? `${monitors.length} monitor${monitors.length !== 1 ? 's' : ''}` : 'No monitors' }}
                  </span>
                </div>

              </div>
            </div>

            <!-- SCORE + NARRATIVE — left-accent rule, no card box -->
            <section class="mb-8 animate-slide-up">
              <div
                class="flex flex-col sm:flex-row gap-5 sm:gap-8 pl-5 border-l-[3px] transition-colors duration-700"
                :style="{
                  borderColor: bestScan.score >= 70 ? '#3D8B5E' : bestScan.score >= 40 ? '#C08832' : '#C25544'
                }"
              >
                <!-- Score circle — right-sized, not the page hero -->
                <div class="shrink-0 flex items-start pt-0.5">
                  <ScoreCircle :score="bestScan.score" :grade="bestScan.grade" :size="84" />
                </div>

                <!-- Narrative -->
                <div class="flex-1 min-w-0">
                  <!-- Domain headline -->
                  <div class="flex items-baseline gap-2.5 flex-wrap mb-1.5">
                    <h1 class="font-display text-xl sm:text-2xl font-bold text-primary leading-tight tracking-tight">
                      {{ primaryDomain || 'Your site' }}
                    </h1>
                  </div>

                  <!-- The real signal: score narrative -->
                  <p class="font-body text-[15px] text-secondary leading-snug mb-3 max-w-lg">{{ scoreMessage }}</p>

                  <!-- Mention insight — only when meaningful -->
                  <p v-if="isPro && mentionFoundCount > 0" class="font-display text-xs font-semibold text-accent flex items-center gap-1.5 mb-4 flex-wrap">
                    <svg class="w-3.5 h-3.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z"/>
                    </svg>
                    AI agents cited you in {{ mentionFoundCount }} of {{ mentionTestedCount }} test queries
                    <span v-if="mentionTrend > 0" class="text-score-good">— up {{ mentionTrend }} this week</span>
                    <span v-else-if="mentionTrend < 0" class="text-score-bad">— down {{ Math.abs(mentionTrend) }} this week</span>
                  </p>
                  <p v-else-if="!isPro" class="font-display text-xs text-muted flex items-center gap-1.5 mb-4">
                    <svg class="w-3.5 h-3.5 shrink-0 text-warm-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z"/>
                    </svg>
                    <router-link to="/pricing" class="text-accent hover:text-accent-hover transition-colors underline underline-offset-2 decoration-accent/30">Upgrade to Pro</router-link>
                    &nbsp;to track how often AI agents mention you
                  </p>
                  <div v-else class="mb-4"></div>

                  <!-- QUICK ACTIONS — ghost-first, one primary -->
                  <div class="flex flex-wrap items-center gap-2">

                    <!-- Primary: Re-scan -->
                    <button
                      @click="scanDomain = primaryDomain; handleScan()"
                      :disabled="scanning || !primaryDomain"
                      class="btn-primary text-xs px-3.5 py-1.5 gap-1.5"
                    >
                      <svg v-if="scanning" class="w-3.5 h-3.5 animate-spin shrink-0" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                      </svg>
                      <svg v-else class="w-3.5 h-3.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
                      </svg>
                      {{ scanning ? 'Scanning…' : 'Re-scan' }}
                    </button>

                    <!-- Secondary: Full report -->
                    <router-link
                      v-if="completedScans[0]"
                      :to="`/report/${completedScans[0].scan_id}`"
                      class="btn-secondary text-xs px-3.5 py-1.5 gap-1.5"
                    >
                      <svg class="w-3.5 h-3.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                      </svg>
                      Full report
                    </router-link>

                    <!-- Ghost: Track mentions (Pro) -->
                    <button
                      v-if="isPro && primaryDomain"
                      @click="handleTrackMentions"
                      :disabled="trackingMentions"
                      class="btn-ghost text-xs px-3.5 py-1.5 gap-1.5"
                    >
                      <svg v-if="trackingMentions" class="w-3.5 h-3.5 animate-spin shrink-0" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                      </svg>
                      <svg v-else class="w-3.5 h-3.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"/>
                      </svg>
                      {{ trackingMentions ? 'Tracking…' : 'Track mentions' }}
                    </button>

                    <!-- Ghost: Compare (Pro) -->
                    <router-link
                      v-if="isPro"
                      to="/compare"
                      class="btn-ghost text-xs px-3.5 py-1.5 gap-1.5"
                    >
                      <svg class="w-3.5 h-3.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7"/>
                      </svg>
                      Compare
                    </router-link>

                  </div>
                </div>

                <!-- Mention mini-chart sidebar — large screens, Pro only -->
                <div v-if="isPro && mentions.length > 0" class="hidden lg:flex flex-col shrink-0 w-40 justify-between">
                  <div class="flex items-center justify-between mb-1.5">
                    <span class="font-display text-[10px] font-semibold uppercase tracking-wider text-muted">Mentions</span>
                    <span class="font-display text-[10px] font-bold text-accent bg-accent/8 px-1.5 py-px rounded">Pro</span>
                  </div>
                  <div class="flex-1 min-h-0">
                    <MentionChart :data="mentions" />
                  </div>
                  <div class="flex items-center justify-between mt-2 pt-2 border-t border-border-light">
                    <span class="font-body text-[11px] text-muted tabular-nums">{{ mentionFoundCount }}/{{ mentionTestedCount }}</span>
                    <span v-if="mentionTrend > 0" class="font-display text-[11px] font-bold text-score-good">+{{ mentionTrend }}</span>
                    <span v-else-if="mentionTrend < 0" class="font-display text-[11px] font-bold text-score-bad">{{ mentionTrend }}</span>
                    <span v-else class="font-display text-[11px] text-muted">—</span>
                  </div>
                </div>

              </div>
            </section>

          </template>

          <!-- ── NO SCANS YET ── editorial empty state -->
          <section v-else class="mb-10 animate-slide-up">
            <div class="pl-5 border-l-[3px] border-warm-200">
              <p class="font-display text-[10px] font-semibold uppercase tracking-widest text-muted mb-3">AI Readiness</p>
              <h1 class="font-display text-2xl sm:text-3xl font-bold text-primary leading-tight tracking-tight mb-2">
                Your first scan<br class="sm:hidden" /> starts here.
              </h1>
              <p class="font-body text-sm text-secondary leading-relaxed max-w-md mb-5">
                Enter any domain above. AgentCheck measures exactly how AI agents perceive, cite, and recommend your site — in about 30 seconds.
              </p>
              <!-- Inline feature hints — horizontal, no icon noise -->
              <div class="flex flex-wrap gap-x-6 gap-y-2">
                <span class="flex items-center gap-1.5 font-display text-xs text-muted">
                  <span class="w-1 h-1 rounded-full bg-accent inline-block shrink-0"></span>
                  Scored 0–100
                </span>
                <span class="flex items-center gap-1.5 font-display text-xs text-muted">
                  <span class="w-1 h-1 rounded-full bg-accent inline-block shrink-0"></span>
                  Category breakdown
                </span>
                <span class="flex items-center gap-1.5 font-display text-xs text-muted">
                  <span class="w-1 h-1 rounded-full bg-accent inline-block shrink-0"></span>
                  Actionable fixes
                </span>
                <span class="flex items-center gap-1.5 font-display text-xs text-muted">
                  <span class="w-1 h-1 rounded-full bg-accent inline-block shrink-0"></span>
                  Results in ~30 s
                </span>
              </div>
            </div>
          </section>

          <!-- ============================================================ -->
          <!-- PRO WIDGETS                                                  -->
          <!-- ============================================================ -->
          <template v-if="isPro">

            <!-- ================================================================ -->
            <!-- SECTION 1: Agent Simulator — full width, flagship feature        -->
            <!-- ================================================================ -->
            <section class="mb-8 animate-slide-up" style="animation-delay: 60ms">
              <div class="flex items-baseline justify-between mb-4">
                <h2 class="font-display text-xs font-bold uppercase tracking-widest text-muted">Agent Simulation</h2>
                <span class="text-[10px] font-display font-bold uppercase tracking-wider text-accent bg-accent/10 px-2 py-0.5 rounded-md">Pro</span>
              </div>

              <!-- Terminal-style full-width panel -->
              <div class="rounded-2xl bg-warm-50 border border-border overflow-hidden">
                <!-- Chrome bar -->
                <div class="flex items-center justify-between px-5 sm:px-7 py-3.5 border-b border-border bg-surface">
                  <div class="flex items-center gap-3">
                    <div class="flex gap-1.5" aria-hidden="true">
                      <span class="w-2.5 h-2.5 rounded-full bg-warm-200"></span>
                      <span class="w-2.5 h-2.5 rounded-full bg-warm-200"></span>
                      <span class="w-2.5 h-2.5 rounded-full bg-warm-200"></span>
                    </div>
                    <p class="font-display font-semibold text-sm text-primary">
                      AI Agent — {{ primaryDomain || 'your site' }}
                    </p>
                  </div>
                  <template v-if="simulation?.steps">
                    <div class="flex items-center gap-2">
                      <span
                        class="w-1.5 h-1.5 rounded-full animate-pulse shrink-0"
                        :class="simulationRate >= 70 ? 'bg-score-good' : simulationRate >= 40 ? 'bg-score-medium' : 'bg-score-bad'"
                      ></span>
                      <span class="text-xs font-display font-bold tabular-nums" :class="scoreColorClass(simulationRate)">{{ simulationRate }}% success rate</span>
                    </div>
                  </template>
                </div>

                <!-- Body -->
                <div class="px-5 sm:px-7 py-5 sm:py-6">
                  <template v-if="simulation?.steps">
                    <!-- Slim progress track -->
                    <div class="mb-6">
                      <div class="w-full h-1 rounded-full bg-warm-200 overflow-hidden">
                        <div
                          class="h-full rounded-full transition-all duration-700 ease-out"
                          :class="{
                            'bg-score-good': simulationRate >= 70,
                            'bg-score-medium': simulationRate >= 40 && simulationRate < 70,
                            'bg-score-bad': simulationRate < 40,
                          }"
                          :style="{ width: simulationRate + '%' }"
                        />
                      </div>
                      <div class="flex items-center gap-5 mt-2">
                        <span class="flex items-center gap-1.5 text-[11px] text-muted font-body">
                          <span class="w-1.5 h-1.5 rounded-full bg-score-good inline-block"></span>Pass
                        </span>
                        <span class="flex items-center gap-1.5 text-[11px] text-muted font-body">
                          <span class="w-1.5 h-1.5 rounded-full bg-score-bad inline-block"></span>Fail
                        </span>
                        <span class="flex items-center gap-1.5 text-[11px] text-muted font-body">
                          <span class="w-1.5 h-1.5 rounded-full bg-warm-300 inline-block"></span>Blocked
                        </span>
                      </div>
                    </div>
                    <!-- Steps rendered in 2-col on larger screens -->
                    <div class="sm:columns-2 sm:gap-x-10">
                      <StepFlow :steps="simulation.steps" />
                    </div>
                    <!-- Footer -->
                    <div class="mt-6 pt-4 border-t border-border-light flex items-center justify-between gap-4">
                      <p class="text-xs text-muted font-body">Reflects your most recent scan result.</p>
                      <button
                        @click="handleSimulate"
                        :disabled="simulating || !latestCompletedScan"
                        class="inline-flex items-center gap-1.5 text-xs font-display font-semibold text-accent hover:text-accent-hover transition-colors disabled:opacity-50 shrink-0"
                      >
                        <svg v-if="simulating" class="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24">
                          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                        </svg>
                        <svg v-else class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                          <path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                        </svg>
                        {{ simulating ? 'Running...' : 'Re-run simulation' }}
                      </button>
                    </div>
                  </template>

                  <template v-else>
                    <div class="flex flex-col sm:flex-row items-start sm:items-center gap-5 sm:gap-8 py-1">
                      <div class="flex-1">
                        <p class="font-display font-bold text-base text-primary mb-1.5">See your site through an AI agent's eyes</p>
                        <p class="text-sm text-secondary font-body leading-relaxed max-w-prose">
                          Step-by-step simulation of how AI agents navigate, parse, and understand every page — with pass/fail results for each action.
                        </p>
                      </div>
                      <button
                        @click="handleSimulate"
                        :disabled="simulating || !latestCompletedScan"
                        class="btn-primary text-sm px-6 py-3 rounded-xl disabled:opacity-50 shrink-0 min-h-[44px]"
                      >
                        <svg v-if="simulating" class="w-4 h-4 animate-spin inline mr-2" fill="none" viewBox="0 0 24 24">
                          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                        </svg>
                        {{ simulating ? 'Running simulation...' : 'Run simulation' }}
                      </button>
                    </div>
                  </template>
                </div>
              </div>
            </section>

            <!-- ================================================================ -->
            <!-- SECTION 2: Intelligence pair — asymmetric 7/5 columns           -->
            <!-- ================================================================ -->
            <section class="mb-8 animate-slide-up" style="animation-delay: 120ms">
              <div class="flex items-baseline justify-between mb-4">
                <h2 class="font-display text-xs font-bold uppercase tracking-widest text-muted">How AI Agents See You</h2>
              </div>

              <div class="grid sm:grid-cols-12 gap-5">

                <!-- AI Mentions (7/12) -->
                <div class="sm:col-span-7 border border-border rounded-xl p-5 sm:p-6 bg-surface">
                  <div class="flex items-start justify-between mb-5">
                    <div>
                      <p class="font-display font-bold text-sm text-primary mb-0.5">AI Mentions</p>
                      <p class="text-xs text-secondary font-body">How often AI models recommend your site</p>
                    </div>
                    <div v-if="mentionFoundCount > 0 || mentionTestedCount > 0" class="text-right shrink-0 ml-4">
                      <p
                        class="font-display font-bold text-2xl tabular-nums leading-none"
                        :class="mentionTestedCount > 0 && mentionFoundCount / mentionTestedCount > 0.5 ? 'text-score-good' : mentionFoundCount > 0 ? 'text-score-medium' : 'text-score-bad'"
                      >
                        {{ mentionFoundCount }}<span class="text-sm text-muted font-normal">/{{ mentionTestedCount }}</span>
                      </p>
                      <p class="text-[10px] text-muted font-body mt-0.5">queries this week</p>
                    </div>
                  </div>

                  <template v-if="mentions.length > 0">
                    <div class="mb-4">
                      <MentionChart :data="mentions" />
                    </div>
                    <div class="flex items-center justify-between pt-3 border-t border-border-light">
                      <p class="text-xs text-secondary font-body">8-week trend</p>
                      <span v-if="mentionTrend > 0" class="inline-flex items-center gap-1 text-xs text-score-good font-display font-semibold">
                        <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                          <path stroke-linecap="round" stroke-linejoin="round" d="M5 15l7-7 7 7" />
                        </svg>
                        +{{ mentionTrend }} vs last week
                      </span>
                      <span v-else-if="mentionTrend < 0" class="inline-flex items-center gap-1 text-xs text-score-bad font-display font-semibold">
                        <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                          <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
                        </svg>
                        {{ mentionTrend }} vs last week
                      </span>
                      <span v-else class="text-xs text-muted font-display">Stable</span>
                    </div>
                  </template>

                  <template v-else>
                    <div class="flex flex-col gap-3 py-1">
                      <p class="text-sm text-secondary font-body leading-relaxed">
                        Track how often AI models like ChatGPT, Claude, and Gemini mention your site in their responses.
                      </p>
                      <button
                        @click="handleTrackMentions"
                        :disabled="trackingMentions || !primaryDomain"
                        class="inline-flex items-center gap-1.5 text-xs font-display font-semibold text-accent hover:text-accent-hover transition-colors disabled:opacity-50 min-h-[44px] w-fit"
                      >
                        <svg v-if="trackingMentions" class="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24">
                          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                        </svg>
                        <svg v-else class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                          <path stroke-linecap="round" stroke-linejoin="round" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                        </svg>
                        {{ trackingMentions ? 'Tracking...' : 'Start tracking mentions' }}
                      </button>
                    </div>
                  </template>
                </div>

                <!-- Competitors (5/12) -->
                <div class="sm:col-span-5 border border-border rounded-xl p-5 sm:p-6 bg-surface flex flex-col">
                  <div class="flex items-start justify-between mb-4">
                    <div>
                      <p class="font-display font-bold text-sm text-primary mb-0.5">Competitors</p>
                      <p class="text-xs text-secondary font-body">AI visibility leaderboard</p>
                    </div>
                    <router-link
                      v-if="competitors.length > 0"
                      :to="{ path: '/compare' }"
                      class="inline-flex items-center gap-1 text-xs text-accent hover:text-accent-hover font-display font-semibold transition-colors shrink-0 ml-3 mt-0.5"
                    >
                      Compare
                      <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
                      </svg>
                    </router-link>
                  </div>

                  <template v-if="shownCompetitors.length > 0">
                    <div class="flex-1 space-y-0.5">
                      <!-- Your domain row -->
                      <div v-if="bestScan" class="flex items-center gap-2.5 px-3 py-2.5 rounded-lg bg-accent/5 border border-accent/10">
                        <span class="text-[9px] font-display font-bold text-accent bg-accent/15 w-5 h-5 rounded flex items-center justify-center shrink-0 uppercase tracking-wide">You</span>
                        <span class="text-xs font-display font-medium text-accent truncate flex-1 min-w-0">{{ primaryDomain }}</span>
                        <span class="text-sm font-display font-bold tabular-nums shrink-0" :class="scoreColorClass(bestScan.score)">{{ bestScan.score }}</span>
                      </div>
                      <!-- Competitor rows -->
                      <div
                        v-for="(comp, idx) in shownCompetitors"
                        :key="comp.competitor_domain || comp.domain"
                        class="flex items-center gap-2.5 px-3 py-2.5 rounded-lg hover:bg-warm-50 transition-colors group"
                      >
                        <span class="text-[10px] font-display font-bold text-warm-400 w-5 h-5 rounded bg-warm-100 group-hover:bg-warm-200 flex items-center justify-center shrink-0 transition-colors">{{ idx + 1 }}</span>
                        <span class="text-xs font-display font-medium text-primary truncate flex-1 min-w-0">{{ comp.competitor_domain || comp.domain }}</span>
                        <span class="text-sm font-display font-bold tabular-nums shrink-0" :class="scoreColorClass(comp.last_score ?? comp.score)">
                          {{ comp.last_score ?? comp.score ?? '--' }}
                        </span>
                      </div>
                    </div>
                    <p v-if="competitors.length > 5" class="text-xs text-muted font-body mt-3 text-center">
                      +{{ competitors.length - 5 }} more tracked
                    </p>
                  </template>

                  <template v-else>
                    <div class="flex-1 flex flex-col justify-between gap-4 py-1">
                      <p class="text-sm text-secondary font-body leading-relaxed">
                        Find and track competitors to compare AI visibility scores side by side.
                      </p>
                      <button
                        @click="handleDiscoverCompetitors"
                        :disabled="discoveringComps || !primaryDomain"
                        class="btn-primary text-sm px-5 py-2.5 rounded-lg disabled:opacity-50 min-h-[44px] w-fit"
                      >
                        <svg v-if="discoveringComps" class="w-4 h-4 animate-spin inline mr-2" fill="none" viewBox="0 0 24 24">
                          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                        </svg>
                        {{ discoveringComps ? 'Discovering...' : 'Discover competitors' }}
                      </button>
                    </div>
                  </template>
                </div>

              </div>
            </section>

            <!-- ================================================================ -->
            <!-- SECTION 3: Keep Your Site Fresh — automation strip + advisory   -->
            <!-- ================================================================ -->
            <section class="mb-8 animate-slide-up" style="animation-delay: 180ms">
              <div class="flex items-baseline justify-between mb-4">
                <h2 class="font-display text-xs font-bold uppercase tracking-widest text-muted">Keep Your Site Fresh</h2>
              </div>

              <div class="space-y-3">

                <!-- Automation strip: Hosted Files + Crawler Status -->
                <div class="rounded-xl border border-border bg-surface overflow-hidden">
                  <div class="grid sm:grid-cols-2 divide-y sm:divide-y-0 sm:divide-x divide-border-light">

                    <!-- Hosted Files panel -->
                    <div class="px-4 sm:px-5 py-4">
                      <div class="flex items-center justify-between mb-3">
                        <div class="flex items-center gap-2">
                          <svg class="w-3.5 h-3.5 text-accent shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                          </svg>
                          <p class="font-display font-semibold text-xs text-primary">AI Files</p>
                          <span v-if="filesActive" class="text-[9px] font-display font-bold uppercase tracking-wider text-score-good bg-score-good/10 px-1.5 py-0.5 rounded">Live</span>
                        </div>
                        <button
                          v-if="!filesActive"
                          @click="handleActivateFiles"
                          :disabled="activatingFiles || !primaryDomain"
                          class="inline-flex items-center gap-1 text-[11px] font-display font-semibold text-accent hover:text-accent-hover transition-colors disabled:opacity-50"
                        >
                          <svg v-if="activatingFiles" class="w-3 h-3 animate-spin" fill="none" viewBox="0 0 24 24">
                            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                          </svg>
                          {{ activatingFiles ? 'Activating...' : 'Activate' }}
                        </button>
                      </div>

                      <template v-if="filesActive">
                        <div class="flex flex-wrap gap-1.5">
                          <div
                            v-for="file in hostedFiles"
                            :key="file.id || file.file_type"
                            class="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-warm-50 border border-border-light group"
                          >
                            <span class="text-[11px] font-display font-semibold text-primary">{{ file.file_type }}</span>
                            <button
                              @click.prevent="copyToClipboard(hostedUrl(file))"
                              class="text-muted hover:text-accent transition-colors"
                              :title="hostedUrl(file)"
                              :aria-label="`Copy URL for ${file.file_type}`"
                            >
                              <svg v-if="copiedUrl === hostedUrl(file)" class="w-3 h-3 text-score-good" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                                <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
                              </svg>
                              <svg v-else class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                                <path stroke-linecap="round" stroke-linejoin="round" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                              </svg>
                            </button>
                          </div>
                        </div>
                        <p class="text-[11px] text-muted font-body mt-2">
                          <template v-if="hostedFiles[0]?.updated_at">Updated {{ formatDate(hostedFiles[0].updated_at) }}</template>
                          <template v-else>Active and serving to crawlers</template>
                        </p>
                      </template>

                      <template v-else>
                        <p class="text-xs text-secondary font-body leading-relaxed">
                          Host <strong class="font-semibold text-primary">llms.txt</strong> and <strong class="font-semibold text-primary">robots.txt</strong> to guide AI crawlers.
                        </p>
                      </template>
                    </div>

                    <!-- Crawler Status panel -->
                    <div class="px-4 sm:px-5 py-4">
                      <div class="flex items-center justify-between mb-3">
                        <div class="flex items-center gap-2">
                          <svg class="w-3.5 h-3.5 text-accent shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M8.111 16.404a5.5 5.5 0 017.778 0M12 20h.01m-7.08-7.071c3.904-3.905 10.236-3.905 14.14 0M1.394 9.393c5.857-5.858 15.355-5.858 21.213 0" />
                          </svg>
                          <p class="font-display font-semibold text-xs text-primary">Crawler Pings</p>
                        </div>
                        <button
                          @click="handlePing"
                          :disabled="pinging || pingsRemaining <= 0"
                          class="inline-flex items-center gap-1 text-[11px] font-display font-semibold text-accent hover:text-accent-hover transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                        >
                          <svg v-if="pinging" class="w-3 h-3 animate-spin" fill="none" viewBox="0 0 24 24">
                            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                          </svg>
                          <svg v-else class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M5.636 18.364a9 9 0 010-12.728m12.728 0a9 9 0 010 12.728M12 12v.01" />
                          </svg>
                          {{ pinging ? 'Pinging...' : 'Ping now' }}
                        </button>
                      </div>

                      <div class="flex items-center gap-4 mb-2.5">
                        <div>
                          <p class="font-display font-bold text-xl tabular-nums text-primary leading-none">{{ pingHistory.length }}</p>
                          <p class="text-[10px] text-muted font-body mt-0.5">total pings</p>
                        </div>
                        <div class="w-px h-8 bg-border-light"></div>
                        <div>
                          <div class="flex gap-1 mb-0.5">
                            <span
                              v-for="i in 3"
                              :key="i"
                              class="w-2 h-2 rounded-full transition-colors"
                              :class="i <= pingsRemaining ? 'bg-accent' : 'bg-warm-200'"
                            />
                          </div>
                          <p class="text-[10px] text-muted font-body">{{ pingsRemaining }}/3 today</p>
                        </div>
                      </div>

                      <template v-if="recentPings.length > 0">
                        <div class="flex flex-wrap gap-x-3 gap-y-1">
                          <span v-for="(ping, idx) in recentPings" :key="idx" class="inline-flex items-center gap-1 text-[11px] font-body text-secondary">
                            <span
                              class="w-1.5 h-1.5 rounded-full shrink-0"
                              :class="ping.status_code >= 200 && ping.status_code < 400 ? 'bg-score-good' : 'bg-score-bad'"
                            ></span>
                            {{ ping.ping_type }}
                          </span>
                        </div>
                      </template>
                      <p v-else class="text-xs text-muted font-body">No pings yet. Notify crawlers to re-index.</p>
                    </div>
                  </div>
                </div>

                <!-- Content Suggestions: left-border advisory panel -->
                <div class="rounded-r-xl border border-border-light border-l-2 border-l-accent/40 pl-4 pr-4 sm:pr-5 py-4 bg-surface">
                  <div class="flex items-start gap-3">
                    <svg class="w-4 h-4 text-accent mt-0.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                    </svg>
                    <div class="flex-1 min-w-0">
                      <div class="flex items-center gap-2.5 mb-1.5">
                        <p class="font-display font-semibold text-sm text-primary">Content Suggestions</p>
                        <span v-if="suggestionCount > 0" class="text-[10px] font-display font-bold bg-accent text-white px-1.5 py-0.5 rounded-full tabular-nums">{{ suggestionCount }}</span>
                      </div>

                      <template v-if="suggestionCount > 0">
                        <p class="text-sm text-secondary font-body mb-2.5">
                          {{ suggestionCount }} improvement{{ suggestionCount > 1 ? 's' : '' }} identified to boost your AI visibility score.
                        </p>
                        <button
                          @click="suggestionsExpanded = !suggestionsExpanded"
                          class="inline-flex items-center gap-1.5 text-xs font-display font-semibold text-accent hover:text-accent-hover transition-colors min-h-[44px] sm:min-h-0"
                        >
                          <svg
                            class="w-3.5 h-3.5 transition-transform duration-200"
                            :class="suggestionsExpanded ? 'rotate-180' : ''"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                            stroke-width="2"
                          >
                            <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
                          </svg>
                          {{ suggestionsExpanded ? 'Collapse suggestions' : 'View all suggestions' }}
                        </button>

                        <div v-if="suggestionsExpanded" class="mt-4 space-y-4">
                          <div
                            v-for="(sugg, idx) in contentSuggs.suggestions"
                            :key="idx"
                            class="pt-4 border-t border-border-light first:pt-0 first:border-0"
                          >
                            <div class="flex items-start justify-between gap-2 mb-1.5">
                              <p class="text-sm font-display font-semibold text-primary">{{ sugg.element || sugg.title || `Suggestion ${idx + 1}` }}</p>
                              <span class="text-[10px] font-display font-bold text-warm-400 bg-warm-100 px-1.5 py-0.5 rounded shrink-0 tabular-nums">#{{ idx + 1 }}</span>
                            </div>
                            <p v-if="sugg.reason" class="text-xs text-muted font-body mb-3 leading-relaxed">{{ sugg.reason }}</p>
                            <div v-if="sugg.current" class="mb-2">
                              <p class="text-[10px] text-muted uppercase tracking-wider font-display font-semibold mb-1">Current</p>
                              <p class="text-xs text-secondary font-body bg-score-bad/5 border border-score-bad/10 rounded-lg p-2.5 leading-relaxed break-words">{{ sugg.current }}</p>
                            </div>
                            <div v-if="sugg.suggested">
                              <p class="text-[10px] text-muted uppercase tracking-wider font-display font-semibold mb-1">Suggested</p>
                              <div class="flex items-start gap-2">
                                <p class="text-xs text-primary font-body bg-score-good/5 border border-score-good/10 rounded-lg p-2.5 flex-1 leading-relaxed break-words">{{ sugg.suggested }}</p>
                                <button
                                  @click="copyToClipboard(sugg.suggested)"
                                  class="shrink-0 mt-1 inline-flex items-center gap-1 text-[11px] font-display font-medium px-2 py-1 rounded-lg transition-all"
                                  :class="copiedUrl === sugg.suggested ? 'bg-score-good/10 text-score-good' : 'bg-warm-100 text-secondary hover:bg-accent/10 hover:text-accent'"
                                >
                                  <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                                    <path stroke-linecap="round" stroke-linejoin="round" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                                  </svg>
                                  {{ copiedUrl === sugg.suggested ? 'Copied' : 'Copy' }}
                                </button>
                              </div>
                            </div>
                          </div>
                        </div>
                      </template>

                      <template v-else>
                        <div class="flex flex-col sm:flex-row sm:items-center gap-3">
                          <p class="text-sm text-secondary font-body leading-relaxed flex-1">
                            Get AI-powered content improvements tailored to your site.
                          </p>
                          <button
                            @click="handleOptimize"
                            :disabled="optimizing || !latestCompletedScan"
                            class="btn-primary text-sm px-5 py-2 rounded-lg disabled:opacity-50 min-h-[44px] shrink-0 w-fit"
                          >
                            <svg v-if="optimizing" class="w-4 h-4 animate-spin inline mr-2" fill="none" viewBox="0 0 24 24">
                              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                            </svg>
                            {{ optimizing ? 'Generating...' : 'Generate suggestions' }}
                          </button>
                        </div>
                      </template>
                    </div>
                  </div>
                </div>

              </div>
            </section>

          </template>
          <!-- END PRO WIDGETS -->

          <!-- ============================================================ -->
          <!-- FREE USER: Persuasive Pro Preview with real-looking data     -->
          <!-- ============================================================ -->
          <template v-if="!isPro && completedScans.length > 0">
            <section class="mb-8 animate-slide-up" style="animation-delay: 80ms">
              <div class="flex items-baseline justify-between mb-4">
                <h2 class="font-display text-xs font-bold uppercase tracking-widest text-muted">Pro Intelligence</h2>
                <span class="text-[10px] font-display font-bold uppercase tracking-wider text-warm-400 bg-warm-100 px-2 py-0.5 rounded-md">Locked</span>
              </div>

              <div class="relative rounded-2xl border border-border overflow-hidden">
                <!-- Fake content preview with real-looking data -->
                <div class="p-5 sm:p-6 opacity-50 blur-[3px] pointer-events-none select-none" aria-hidden="true">

                  <!-- Fake simulator header -->
                  <div class="rounded-xl bg-warm-50 border border-border mb-4 overflow-hidden">
                    <div class="flex items-center gap-3 px-5 py-3 border-b border-border bg-surface">
                      <div class="flex gap-1.5">
                        <span class="w-2.5 h-2.5 rounded-full bg-warm-200"></span>
                        <span class="w-2.5 h-2.5 rounded-full bg-warm-200"></span>
                        <span class="w-2.5 h-2.5 rounded-full bg-warm-200"></span>
                      </div>
                      <p class="font-display font-semibold text-sm text-primary">AI Agent — {{ primaryDomain || 'yoursite.com' }}</p>
                      <span class="ml-auto text-xs font-display font-bold text-score-good">82% success rate</span>
                    </div>
                    <div class="px-5 py-4 space-y-2.5">
                      <div class="w-full h-1 rounded-full bg-warm-200 overflow-hidden">
                        <div class="h-full w-4/5 rounded-full bg-score-good"></div>
                      </div>
                      <div class="flex items-center gap-3">
                        <span class="w-5 h-5 rounded-full bg-score-good flex items-center justify-center shrink-0">
                          <svg class="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" /></svg>
                        </span>
                        <span class="text-sm text-primary font-body">Fetched llms.txt successfully</span>
                      </div>
                      <div class="flex items-center gap-3">
                        <span class="w-5 h-5 rounded-full bg-score-good flex items-center justify-center shrink-0">
                          <svg class="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" /></svg>
                        </span>
                        <span class="text-sm text-primary font-body">Parsed structured data on homepage</span>
                      </div>
                      <div class="flex items-center gap-3">
                        <span class="w-5 h-5 rounded-full bg-score-bad flex items-center justify-center shrink-0">
                          <svg class="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>
                        </span>
                        <span class="text-sm text-score-bad font-body">No contact/about page found for attribution</span>
                      </div>
                    </div>
                  </div>

                  <!-- Fake intelligence row -->
                  <div class="grid sm:grid-cols-2 gap-4">
                    <div class="border border-border rounded-xl p-4 bg-surface">
                      <p class="font-display font-bold text-sm text-primary mb-1">AI Mentions</p>
                      <p class="text-xs text-secondary font-body mb-3">Mentioned in 7/12 AI queries</p>
                      <div class="flex items-end gap-1 h-10">
                        <div class="flex-1 rounded-t bg-score-medium" style="height:30%"></div>
                        <div class="flex-1 rounded-t bg-score-medium" style="height:45%"></div>
                        <div class="flex-1 rounded-t bg-score-good" style="height:60%"></div>
                        <div class="flex-1 rounded-t bg-score-good" style="height:55%"></div>
                        <div class="flex-1 rounded-t bg-score-good" style="height:75%"></div>
                        <div class="flex-1 rounded-t bg-score-good" style="height:80%"></div>
                        <div class="flex-1 rounded-t bg-score-good" style="height:90%"></div>
                        <div class="flex-1 rounded-t bg-score-good" style="height:100%"></div>
                      </div>
                    </div>
                    <!-- Competitor leaderboard showing them losing -->
                    <div class="border border-border rounded-xl p-4 bg-surface">
                      <p class="font-display font-bold text-sm text-primary mb-3">Competitors</p>
                      <div class="space-y-1.5">
                        <div class="flex items-center gap-2.5 px-2.5 py-2 rounded-lg bg-score-bad/5 border border-score-bad/10">
                          <span class="text-[9px] font-display font-bold text-score-bad bg-score-bad/15 w-5 h-5 rounded flex items-center justify-center uppercase">1st</span>
                          <span class="text-xs font-display font-medium text-primary truncate flex-1">competitor.com</span>
                          <span class="text-sm font-display font-bold text-score-good tabular-nums">87</span>
                        </div>
                        <div class="flex items-center gap-2.5 px-2.5 py-2 rounded-lg bg-accent/5 border border-accent/10">
                          <span class="text-[9px] font-display font-bold text-accent bg-accent/15 w-5 h-5 rounded flex items-center justify-center uppercase">You</span>
                          <span class="text-xs font-display font-medium text-accent truncate flex-1">{{ primaryDomain || 'yoursite.com' }}</span>
                          <span class="text-sm font-display font-bold tabular-nums" :class="scoreColorClass(bestScan?.score)">{{ bestScan?.score ?? '—' }}</span>
                        </div>
                        <div class="flex items-center gap-2.5 px-2.5 py-2 rounded-lg">
                          <span class="text-[10px] font-display font-bold text-warm-400 bg-warm-100 w-5 h-5 rounded flex items-center justify-center">3</span>
                          <span class="text-xs font-display font-medium text-primary truncate flex-1">rival-brand.io</span>
                          <span class="text-sm font-display font-bold text-score-medium tabular-nums">61</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- Frosted overlay CTA -->
                <div class="absolute inset-0 flex flex-col items-center justify-center bg-surface/70 backdrop-blur-[6px]">
                  <div class="text-center px-6 max-w-sm">
                    <div class="inline-flex items-center gap-1.5 text-[10px] font-display font-bold uppercase tracking-widest text-accent bg-accent/10 px-3 py-1.5 rounded-full mb-4">
                      <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                      </svg>
                      Pro only
                    </div>
                    <p class="font-display text-xl font-bold text-primary mb-2">A competitor is already beating you</p>
                    <p class="text-sm text-secondary font-body leading-relaxed mb-6">
                      See exactly where you rank, why AI agents prefer competitors, and get a step-by-step simulation to close the gap.
                    </p>
                    <router-link to="/pricing" class="btn-primary text-sm px-7 py-3 rounded-xl shadow-sm inline-flex items-center gap-2">
                      Upgrade to Pro
                      <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
                      </svg>
                    </router-link>
                    <p class="text-xs text-muted font-body mt-3">Cancel anytime. Results in minutes.</p>
                  </div>
                </div>
              </div>
            </section>
          </template>

          <!-- ============================================================ -->
          <!-- RECENT SCANS                                                 -->
          <!-- ============================================================ -->
          <section class="mb-10 animate-slide-up" :style="{ animationDelay: isPro ? '240ms' : '120ms' }">
            <div class="flex items-center justify-between mb-4">
              <h2 class="font-display text-xs font-bold uppercase tracking-widest text-muted">Scan History</h2>
              <div class="flex items-center gap-3">
                <!-- View all link: shown when >5 scans -->
                <router-link
                  v-if="scans.length > 5"
                  to="/history"
                  class="text-xs font-display font-semibold text-accent hover:text-accent-hover transition-colors"
                >
                  View all {{ scans.length }}
                  <svg class="w-3 h-3 inline ml-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
                  </svg>
                </router-link>
              </div>
            </div>

            <!-- Empty: only shown when hero empty state is hidden (scans exist but none completed — shouldn't normally happen) -->
            <div v-if="scans.length === 0" class="rounded-xl border border-dashed border-border py-10 text-center bg-surface/50">
              <p class="text-sm text-muted font-body">No scans yet. Run your first scan above.</p>
            </div>

            <!-- Table-like audit ledger -->
            <div v-else class="border border-border rounded-xl bg-surface overflow-hidden">
              <!-- Column header -->
              <div class="hidden sm:grid grid-cols-[1fr_auto_auto_auto] gap-4 px-5 py-2.5 border-b border-border-light bg-warm-50/60">
                <span class="text-[10px] font-display font-bold uppercase tracking-wider text-warm-400">Domain</span>
                <span class="text-[10px] font-display font-bold uppercase tracking-wider text-warm-400 text-right w-16">Score</span>
                <span class="text-[10px] font-display font-bold uppercase tracking-wider text-warm-400 text-right w-20">Date</span>
                <span class="w-6" />
              </div>

              <!-- Rows -->
              <div class="divide-y divide-border-light">
                <router-link
                  v-for="scan in recentScans.slice(0, 5)"
                  :key="scan.scan_id"
                  :to="scan.status === 'completed' ? { name: 'Report', params: { id: scan.scan_id } } : { name: 'ScanProgress', params: { id: scan.scan_id } }"
                  class="group relative flex sm:grid sm:grid-cols-[1fr_auto_auto_auto] items-center gap-3 sm:gap-4 px-5 py-3.5 hover:bg-warm-50 transition-all duration-150 cursor-pointer"
                  style="--tw-translate-x: 0;"
                >
                  <!-- Slide-right indicator on hover -->
                  <span class="absolute left-0 top-0 bottom-0 w-0.5 bg-accent scale-y-0 group-hover:scale-y-100 transition-transform duration-200 origin-center rounded-r-full" />

                  <!-- Domain + meta -->
                  <div class="flex items-center gap-3 min-w-0 flex-1">
                    <!-- Score dot -->
                    <span
                      class="shrink-0 w-2 h-2 rounded-full mt-0.5"
                      :class="{
                        'bg-score-good': scan.status === 'completed' && scan.score != null && scan.score >= 70,
                        'bg-score-medium': scan.status === 'completed' && scan.score != null && scan.score >= 40 && scan.score < 70,
                        'bg-score-bad': scan.status === 'completed' && scan.score != null && scan.score < 40,
                        'bg-accent animate-pulse': scan.status === 'running' || scan.status === 'pending',
                        'bg-warm-300': scan.status !== 'completed' && scan.status !== 'running' && scan.status !== 'pending',
                      }"
                    />
                    <div class="min-w-0">
                      <p class="text-sm font-display font-semibold text-primary truncate group-hover:text-accent transition-colors duration-150 leading-snug">
                        {{ scan.domain }}
                      </p>
                      <!-- Mobile: show date inline below domain -->
                      <p class="sm:hidden text-[11px] text-warm-400 font-body mt-0.5 leading-none">
                        <span v-if="scan.created_at">{{ formatDate(scan.created_at) }}</span>
                        <span v-if="scan.status === 'running' || scan.status === 'pending'" class="text-accent">Scanning...</span>
                      </p>
                    </div>
                    <span
                      v-if="scan.site_type"
                      class="hidden sm:inline text-[10px] font-display font-medium uppercase tracking-wider text-warm-500 bg-warm-100 px-1.5 py-0.5 rounded-md shrink-0"
                    >
                      {{ scan.site_type }}
                    </span>
                  </div>

                  <!-- Score number + grade pill -->
                  <div class="shrink-0 flex items-center gap-2 w-auto sm:w-16 justify-end">
                    <template v-if="scan.status === 'completed' && scan.score != null">
                      <span
                        class="font-display font-bold text-sm tabular-nums"
                        :class="{
                          'text-score-good': scan.score >= 70,
                          'text-score-medium': scan.score >= 40 && scan.score < 70,
                          'text-score-bad': scan.score < 40,
                        }"
                      >{{ scan.score }}</span>
                      <span
                        class="font-display font-semibold text-[10px] px-1.5 py-0.5 rounded-md leading-none"
                        :class="{
                          'bg-score-good/10 text-score-good': scan.score >= 70,
                          'bg-score-medium/10 text-score-medium': scan.score >= 40 && scan.score < 70,
                          'bg-score-bad/10 text-score-bad': scan.score < 40,
                        }"
                      >{{ scan.grade }}</span>
                    </template>
                    <span v-else-if="scan.status === 'running' || scan.status === 'pending'" class="text-[11px] text-accent font-display font-medium">—</span>
                    <span v-else class="text-[11px] text-score-bad font-display font-medium">Err</span>
                  </div>

                  <!-- Date — desktop only -->
                  <div class="hidden sm:block shrink-0 w-20 text-right">
                    <span v-if="scan.created_at" class="text-xs text-warm-400 font-body tabular-nums">{{ formatDate(scan.created_at) }}</span>
                    <span v-else class="text-xs text-accent font-display animate-pulse">Running...</span>
                  </div>

                  <!-- Actions: delete always on mobile, hover on desktop -->
                  <div class="shrink-0 flex items-center gap-1 w-6">
                    <button
                      @click.prevent.stop="handleDeleteScan(scan.scan_id)"
                      class="w-6 h-6 rounded-md flex items-center justify-center text-warm-300 hover:text-score-bad hover:bg-score-bad/10 transition-colors sm:opacity-0 sm:group-hover:opacity-100 focus:opacity-100"
                      title="Delete scan"
                      aria-label="Delete scan"
                    >
                      <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  </div>
                </router-link>
              </div>

              <!-- Footer: view all if >5 scans -->
              <div v-if="scans.length > 5" class="border-t border-border-light px-5 py-3 bg-warm-50/40 flex items-center justify-between">
                <span class="text-xs text-warm-400 font-body">Showing 5 of {{ scans.length }} scans</span>
                <router-link
                  to="/history"
                  class="inline-flex items-center gap-1 text-xs font-display font-semibold text-accent hover:text-accent-hover transition-colors"
                >
                  View all
                  <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
                  </svg>
                </router-link>
              </div>
            </div>
          </section>

          <!-- ============================================================ -->
          <!-- UPGRADE STRIP (free users, bottom)                           -->
          <!-- ============================================================ -->
          <section v-if="!isPro" class="mb-10 animate-slide-up" style="animation-delay: 160ms">
            <div
              class="relative overflow-hidden rounded-xl border border-accent/20"
              style="background: linear-gradient(105deg, #FAF9F7 0%, rgba(13,115,119,0.04) 100%);"
            >
              <!-- Decorative accent line -->
              <div class="absolute left-0 top-0 bottom-0 w-0.5 bg-gradient-to-b from-accent/60 via-accent to-accent/20 rounded-l-xl" />

              <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 px-6 sm:px-8 py-5">
                <!-- Left: contextual value prop -->
                <div class="min-w-0">
                  <!-- Dynamic message if they have scan data, generic fallback -->
                  <p class="font-display font-bold text-primary text-sm leading-snug">
                    <template v-if="latestCompletedScan && latestCompletedScan.score != null && latestCompletedScan.score < 70">
                      Your site scores {{ latestCompletedScan.score }} — Pro users improve 2.5&times; faster
                    </template>
                    <template v-else-if="latestCompletedScan && latestCompletedScan.score != null">
                      Strong score. Pro keeps it that way with weekly monitoring &amp; alerts.
                    </template>
                    <template v-else>
                      Make AI agents recommend your site — not your competitors'
                    </template>
                  </p>
                  <p class="text-xs text-secondary font-body mt-1 leading-relaxed">
                    Monitoring, AI discovery tests, competitor analysis, and fix files — all in one place.
                  </p>
                </div>

                <!-- Right: CTA cluster -->
                <div class="flex items-center gap-3 shrink-0">
                  <router-link
                    to="/pricing"
                    class="text-xs text-secondary font-body hover:text-primary transition-colors whitespace-nowrap"
                  >
                    See plans
                  </router-link>
                  <router-link
                    to="/pricing"
                    class="inline-flex items-center gap-2 bg-accent hover:bg-accent-hover text-white text-sm font-display font-semibold px-5 py-2.5 rounded-lg transition-colors whitespace-nowrap shadow-sm"
                  >
                    Upgrade to Pro
                    <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" />
                    </svg>
                  </router-link>
                </div>
              </div>
            </div>
          </section>

        </template>
      </div>
    </div>
  </AppLayout>
</template>
