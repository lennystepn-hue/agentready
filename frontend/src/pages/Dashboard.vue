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

// ---- AI Visibility Status (new computed properties) ----

const visibilityTier = computed(() => {
  const s = bestScan.value?.score
  if (s == null) return null
  if (s >= 70) return 'discoverable'
  if (s >= 40) return 'partial'
  return 'hidden'
})

const visibilityLabel = computed(() => {
  if (visibilityTier.value === 'discoverable') return 'Fully Discoverable'
  if (visibilityTier.value === 'partial') return 'Partially Visible'
  if (visibilityTier.value === 'hidden') return 'Not Found'
  return null
})

const visibilityDesc = computed(() => {
  if (visibilityTier.value === 'discoverable') return 'AI agents can reliably find, parse, and cite your site.'
  if (visibilityTier.value === 'partial') return 'Some AI agents can find you — but gaps are costing you citations.'
  if (visibilityTier.value === 'hidden') return 'AI agents cannot find or recommend your site right now.'
  return ''
})

// Derive per-LLM visibility from score + files state
// A score >= 70 means all major LLMs can likely index you; partial means only some
const llmVisibility = computed(() => {
  const s = bestScan.value?.score ?? 0
  const hasFiles = filesActive.value
  return [
    { name: 'ChatGPT',   visible: s >= 60 && hasFiles },
    { name: 'Claude',    visible: s >= 55 },
    { name: 'Perplexity',visible: s >= 50 },
    { name: 'Gemini',    visible: s >= 65 && hasFiles },
  ]
})

// ---- Quick Actions Checklist (new computed) ----

const quickActions = computed(() => {
  const scan = latestCompletedScan.value
  const actions = []

  if (!scan) return actions

  // llms.txt / hosted files
  actions.push({
    id: 'llms_txt',
    label: 'Activate llms.txt',
    detail: 'Tells AI models exactly what your site does',
    done: filesActive.value,
    actionLabel: filesActive.value ? null : 'Activate',
    action: filesActive.value ? null : handleActivateFiles,
    loading: activatingFiles.value,
  })

  // Crawler ping
  actions.push({
    id: 'crawler_ping',
    label: 'Ping AI crawlers',
    detail: 'Notify bots to re-index your latest content',
    done: pingHistory.value.length > 0,
    actionLabel: pingHistory.value.length > 0 ? null : 'Ping now',
    action: pingHistory.value.length > 0 ? null : handlePing,
    loading: pinging.value,
  })

  // Full report
  actions.push({
    id: 'view_report',
    label: 'Review full AI report',
    detail: 'See every check, fix, and opportunity',
    done: false,
    link: scan ? `/report/${scan.scan_id}` : null,
    actionLabel: 'View report',
  })

  // Mention tracking (Pro)
  if (isPro.value) {
    actions.push({
      id: 'track_mentions',
      label: 'Track AI mentions',
      detail: 'See how often ChatGPT, Claude, and Gemini cite you',
      done: mentions.value.length > 0,
      actionLabel: mentions.value.length > 0 ? null : 'Start tracking',
      action: mentions.value.length > 0 ? null : handleTrackMentions,
      loading: trackingMentions.value,
    })
  }

  // Agent simulation (Pro)
  if (isPro.value) {
    actions.push({
      id: 'simulate',
      label: 'Run agent simulation',
      detail: 'Watch how ChatGPT navigates your site step by step',
      done: !!simulation.value,
      actionLabel: simulation.value ? null : 'Run now',
      action: simulation.value ? null : handleSimulate,
      loading: simulating.value,
    })
  }

  return actions
})

const quickActionsCompleted = computed(() => quickActions.value.filter(a => a.done).length)
const quickActionsTotal = computed(() => quickActions.value.length)
const quickActionsProgress = computed(() =>
  quickActionsTotal.value > 0
    ? Math.round((quickActionsCompleted.value / quickActionsTotal.value) * 100)
    : 0
)

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
        <section class="mb-8 animate-fade-in">
          <div class="relative">
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
              <div class="hidden sm:flex items-center pr-3 shrink-0">
                <kbd class="inline-flex items-center gap-1 rounded border border-border-light px-1.5 py-0.5 text-[10px] font-mono text-warm-400 bg-warm-50 leading-none select-none">
                  ↵ Enter
                </kbd>
              </div>
              <div class="w-px bg-border self-stretch my-2 shrink-0" />
              <button
                type="submit"
                :disabled="scanning || !scanDomain.trim()"
                class="relative flex items-center gap-2 px-5 sm:px-7 py-4 text-sm font-display font-semibold rounded-r-xl transition-all duration-200 shrink-0 disabled:opacity-50 disabled:cursor-not-allowed"
                :class="scanDomain.trim() && !scanning ? 'bg-accent text-white hover:bg-accent-hover' : 'bg-warm-100 text-warm-500'"
              >
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
        <!-- LOADING STATE                                                 -->
        <!-- ============================================================ -->
        <div v-if="loadingScans" class="space-y-5">
          <div class="border border-border rounded-xl p-6 bg-surface animate-pulse">
            <div class="h-3 w-32 rounded-full bg-warm-200 mb-4" />
            <div class="h-16 w-full rounded-lg bg-warm-100 mb-3" />
            <div class="h-10 w-full rounded-lg bg-warm-100" />
          </div>
          <div class="border border-border rounded-xl bg-surface overflow-hidden divide-y divide-border-light">
            <div v-for="i in 4" :key="i" class="flex items-center gap-4 px-5 py-4 animate-pulse">
              <div class="shrink-0 w-8 h-8 rounded-full bg-warm-200" />
              <div class="flex-1 space-y-2">
                <div class="h-3.5 rounded-full bg-warm-200" :style="`width: ${55 + (i * 11) % 30}%`" />
                <div class="h-2.5 w-20 rounded-full bg-warm-100" />
              </div>
              <div class="shrink-0 h-6 w-10 rounded-lg bg-warm-100" />
            </div>
          </div>
        </div>

        <template v-else>

          <!-- ============================================================ -->
          <!-- EMPTY STATE                                                   -->
          <!-- ============================================================ -->
          <section v-if="completedScans.length === 0 && scans.length === 0" class="mb-10 animate-slide-up">
            <div class="pl-5 border-l-[3px] border-warm-200">
              <p class="font-display text-[10px] font-semibold uppercase tracking-widest text-muted mb-3">AI Visibility</p>
              <h1 class="font-display text-2xl sm:text-3xl font-bold text-primary leading-tight tracking-tight mb-2">
                Your first scan<br class="sm:hidden" /> starts here.
              </h1>
              <p class="font-body text-sm text-secondary leading-relaxed max-w-md mb-5">
                Enter any domain above. AgentCheck measures exactly how AI agents perceive, cite, and recommend your site — in about 30 seconds.
              </p>
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
          <!-- HAS SCANS: COMMAND CENTER LAYOUT                             -->
          <!-- ============================================================ -->
          <template v-if="completedScans.length > 0">

            <!-- ============================================================ -->
            <!-- 1. AI VISIBILITY STATUS BANNER                               -->
            <!-- ============================================================ -->
            <section class="mb-6 animate-fade-in">
              <div
                class="relative rounded-2xl border overflow-hidden transition-all duration-700"
                :class="{
                  'border-score-good/30 bg-score-good/4': visibilityTier === 'discoverable',
                  'border-score-medium/30 bg-score-medium/4': visibilityTier === 'partial',
                  'border-score-bad/30 bg-score-bad/4': visibilityTier === 'hidden',
                }"
              >
                <!-- Subtle left accent stripe -->
                <div
                  class="absolute left-0 top-0 bottom-0 w-1 rounded-l-2xl transition-colors duration-700"
                  :class="{
                    'bg-score-good': visibilityTier === 'discoverable',
                    'bg-score-medium': visibilityTier === 'partial',
                    'bg-score-bad': visibilityTier === 'hidden',
                  }"
                />

                <div class="pl-6 pr-5 py-5 sm:py-6">
                  <div class="flex flex-col sm:flex-row sm:items-center gap-5 sm:gap-8">

                    <!-- Status + score block -->
                    <div class="flex items-center gap-4 sm:gap-5 shrink-0">
                      <ScoreCircle :score="bestScan.score" :grade="bestScan.grade" :size="72" />
                      <div>
                        <!-- Tier badge -->
                        <div
                          class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-display font-bold uppercase tracking-wider mb-1.5 transition-all duration-500"
                          :class="{
                            'bg-score-good/12 text-score-good': visibilityTier === 'discoverable',
                            'bg-score-medium/12 text-score-medium': visibilityTier === 'partial',
                            'bg-score-bad/12 text-score-bad': visibilityTier === 'hidden',
                          }"
                        >
                          <span
                            class="w-1.5 h-1.5 rounded-full shrink-0"
                            :class="{
                              'bg-score-good animate-pulse': visibilityTier === 'discoverable',
                              'bg-score-medium': visibilityTier === 'partial',
                              'bg-score-bad': visibilityTier === 'hidden',
                            }"
                          />
                          {{ visibilityLabel }}
                        </div>
                        <h1 class="font-display text-lg sm:text-xl font-bold text-primary leading-tight tracking-tight">
                          {{ primaryDomain }}
                        </h1>
                        <p class="font-body text-xs text-secondary mt-0.5 max-w-xs">{{ visibilityDesc }}</p>
                      </div>
                    </div>

                    <!-- Divider -->
                    <div class="hidden sm:block w-px self-stretch bg-border-light" />

                    <!-- LLM visibility grid -->
                    <div class="flex-1">
                      <p class="section-label mb-3">AI Model Visibility</p>
                      <div class="grid grid-cols-2 sm:grid-cols-4 gap-2">
                        <div
                          v-for="llm in llmVisibility"
                          :key="llm.name"
                          class="flex items-center gap-2 px-2.5 py-2 rounded-lg border transition-colors duration-300"
                          :class="llm.visible
                            ? 'border-score-good/20 bg-score-good/5'
                            : 'border-border-light bg-warm-50/60'"
                        >
                          <span
                            class="w-1.5 h-1.5 rounded-full shrink-0 transition-colors duration-300"
                            :class="llm.visible ? 'bg-score-good' : 'bg-warm-300'"
                          />
                          <span class="font-display text-xs font-semibold text-primary truncate">{{ llm.name }}</span>
                          <span
                            class="ml-auto text-[10px] font-display font-bold shrink-0 transition-colors duration-300"
                            :class="llm.visible ? 'text-score-good' : 'text-warm-400'"
                          >{{ llm.visible ? '✓' : '✗' }}</span>
                        </div>
                      </div>
                    </div>

                    <!-- Actions strip -->
                    <div class="flex sm:flex-col gap-2 shrink-0">
                      <button
                        @click="scanDomain = primaryDomain; handleScan()"
                        :disabled="scanning || !primaryDomain"
                        class="btn-primary text-xs px-3.5 py-2 gap-1.5"
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
                      <router-link
                        v-if="completedScans[0]"
                        :to="`/report/${completedScans[0].scan_id}`"
                        class="btn-secondary text-xs px-3.5 py-2 gap-1.5"
                      >
                        <svg class="w-3.5 h-3.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                          <path stroke-linecap="round" stroke-linejoin="round" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                        </svg>
                        Full report
                      </router-link>
                    </div>

                  </div>
                </div>
              </div>
            </section>

            <!-- ============================================================ -->
            <!-- 2. QUICK ACTIONS CHECKLIST                                    -->
            <!-- ============================================================ -->
            <section class="mb-6 animate-slide-up" style="animation-delay: 60ms">
              <div class="rounded-xl border border-border bg-surface overflow-hidden">
                <!-- Header with progress -->
                <div class="flex items-center justify-between px-5 py-3.5 border-b border-border-light bg-warm-50/50">
                  <div class="flex items-center gap-3">
                    <h2 class="font-display text-xs font-bold uppercase tracking-widest text-muted">Steps to Get Found by AI</h2>
                    <span class="font-display text-[10px] font-bold text-accent bg-accent/10 px-2 py-0.5 rounded-full tabular-nums">
                      {{ quickActionsCompleted }}/{{ quickActionsTotal }} done
                    </span>
                  </div>
                  <!-- Progress bar -->
                  <div class="hidden sm:flex items-center gap-2 shrink-0">
                    <div class="w-24 h-1.5 rounded-full bg-warm-200 overflow-hidden">
                      <div
                        class="h-full rounded-full bg-accent transition-all duration-700 ease-out"
                        :style="{ width: quickActionsProgress + '%' }"
                      />
                    </div>
                    <span class="font-display text-[10px] text-muted font-semibold tabular-nums">{{ quickActionsProgress }}%</span>
                  </div>
                </div>

                <!-- Action rows -->
                <div class="divide-y divide-border-light">
                  <div
                    v-for="action in quickActions"
                    :key="action.id"
                    class="flex items-center gap-4 px-5 py-3.5 transition-colors duration-150"
                    :class="action.done ? 'bg-warm-50/30' : 'hover:bg-warm-50/60'"
                  >
                    <!-- Checkbox indicator -->
                    <div
                      class="shrink-0 w-5 h-5 rounded-full border-2 flex items-center justify-center transition-all duration-300"
                      :class="action.done
                        ? 'border-score-good bg-score-good'
                        : 'border-warm-300 bg-surface'"
                    >
                      <svg v-if="action.done" class="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
                      </svg>
                    </div>

                    <!-- Label + detail -->
                    <div class="flex-1 min-w-0">
                      <p
                        class="font-display text-sm font-semibold leading-tight transition-colors duration-200"
                        :class="action.done ? 'text-muted line-through decoration-warm-300' : 'text-primary'"
                      >{{ action.label }}</p>
                      <p class="font-body text-xs text-secondary mt-0.5">{{ action.detail }}</p>
                    </div>

                    <!-- CTA -->
                    <div class="shrink-0">
                      <template v-if="!action.done && action.actionLabel">
                        <router-link
                          v-if="action.link"
                          :to="action.link"
                          class="inline-flex items-center gap-1 text-xs font-display font-semibold text-accent hover:text-accent-hover transition-colors px-3 py-1.5 rounded-lg border border-accent/20 hover:bg-accent/5"
                        >
                          {{ action.actionLabel }}
                          <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
                          </svg>
                        </router-link>
                        <button
                          v-else-if="action.action"
                          @click="action.action"
                          :disabled="action.loading"
                          class="inline-flex items-center gap-1 text-xs font-display font-semibold text-accent hover:text-accent-hover transition-colors px-3 py-1.5 rounded-lg border border-accent/20 hover:bg-accent/5 disabled:opacity-50"
                        >
                          <svg v-if="action.loading" class="w-3 h-3 animate-spin" fill="none" viewBox="0 0 24 24">
                            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                          </svg>
                          {{ action.loading ? 'Working…' : action.actionLabel }}
                        </button>
                      </template>
                      <span v-else-if="action.done" class="text-[10px] font-display font-bold text-score-good uppercase tracking-wider">Complete</span>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            <!-- ============================================================ -->
            <!-- 3. YOUR AI PRESENCE — Hosted Files + Crawler Ping            -->
            <!-- ============================================================ -->
            <section class="mb-6 animate-slide-up" style="animation-delay: 100ms">
              <div class="rounded-xl border overflow-hidden transition-all duration-500"
                :class="filesActive ? 'border-score-good/25 bg-score-good/3' : 'border-border bg-surface'"
              >
                <!-- Header -->
                <div class="flex items-center justify-between px-5 py-4 border-b transition-colors duration-500"
                  :class="filesActive ? 'border-score-good/15 bg-score-good/5' : 'border-border-light bg-warm-50/50'"
                >
                  <div class="flex items-center gap-2.5">
                    <div
                      class="w-7 h-7 rounded-lg flex items-center justify-center shrink-0 transition-colors duration-500"
                      :class="filesActive ? 'bg-score-good/15' : 'bg-warm-100'"
                    >
                      <svg class="w-3.5 h-3.5 transition-colors duration-500" :class="filesActive ? 'text-score-good' : 'text-warm-500'" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </div>
                    <div>
                      <h2 class="font-display text-sm font-bold text-primary leading-tight">Your AI Presence</h2>
                      <p class="font-body text-xs text-secondary">Hosted files &amp; crawler access</p>
                    </div>
                    <span
                      v-if="filesActive"
                      class="ml-1 text-[9px] font-display font-bold uppercase tracking-wider text-score-good bg-score-good/12 px-2 py-0.5 rounded-full"
                    >Live</span>
                  </div>
                  <span v-if="isPro" class="text-[10px] font-display font-bold uppercase tracking-wider text-accent bg-accent/10 px-2 py-0.5 rounded-md">Pro</span>
                  <span v-else class="text-[10px] font-display font-bold uppercase tracking-wider text-warm-400 bg-warm-100 px-2 py-0.5 rounded-md">Pro</span>
                </div>

                <div class="p-5 sm:p-6">
                  <template v-if="isPro">
                    <div class="grid sm:grid-cols-2 gap-5 sm:gap-6">

                      <!-- Hosted Files panel -->
                      <div>
                        <div class="flex items-center justify-between mb-3">
                          <p class="font-display text-xs font-semibold text-primary flex items-center gap-1.5">
                            <svg class="w-3.5 h-3.5 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                              <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                            AI Files
                          </p>
                        </div>

                        <template v-if="filesActive">
                          <div class="flex flex-wrap gap-1.5 mb-2">
                            <div
                              v-for="file in hostedFiles"
                              :key="file.id || file.file_type"
                              class="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-warm-50 border border-border-light group"
                            >
                              <span class="w-1.5 h-1.5 rounded-full bg-score-good shrink-0"></span>
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
                          <p class="text-[11px] text-muted font-body">
                            <template v-if="hostedFiles[0]?.updated_at">Updated {{ formatDate(hostedFiles[0].updated_at) }}</template>
                            <template v-else>Active and serving to crawlers</template>
                          </p>
                        </template>

                        <template v-else>
                          <p class="text-xs text-secondary font-body leading-relaxed mb-4">
                            Host <strong class="font-semibold text-primary">llms.txt</strong>, <strong class="font-semibold text-primary">ai.txt</strong> and <strong class="font-semibold text-primary">robots.txt</strong> additions directly from AgentCheck — AI crawlers will find and index you automatically.
                          </p>
                          <button
                            @click="handleActivateFiles"
                            :disabled="activatingFiles || !primaryDomain"
                            class="btn-primary text-sm px-5 py-2.5 rounded-lg disabled:opacity-50 gap-2"
                          >
                            <svg v-if="activatingFiles" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                            </svg>
                            <svg v-else class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                              <path stroke-linecap="round" stroke-linejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
                            </svg>
                            {{ activatingFiles ? 'Activating…' : 'Activate AI Presence' }}
                          </button>
                        </template>
                      </div>

                      <!-- Vertical divider on sm+ -->
                      <div class="hidden sm:block absolute left-1/2 top-0 bottom-0 w-px bg-border-light pointer-events-none" aria-hidden="true" style="display:none" />

                      <!-- Crawler Ping panel -->
                      <div class="border-t sm:border-t-0 sm:border-l border-border-light sm:pl-6 pt-4 sm:pt-0">
                        <div class="flex items-center justify-between mb-3">
                          <p class="font-display text-xs font-semibold text-primary flex items-center gap-1.5">
                            <svg class="w-3.5 h-3.5 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                              <path stroke-linecap="round" stroke-linejoin="round" d="M8.111 16.404a5.5 5.5 0 017.778 0M12 20h.01m-7.08-7.071c3.904-3.905 10.236-3.905 14.14 0M1.394 9.393c5.857-5.858 15.355-5.858 21.213 0" />
                            </svg>
                            Crawler Pings
                          </p>
                          <div class="flex items-center gap-1.5">
                            <span v-for="i in 3" :key="i"
                              class="w-2 h-2 rounded-full transition-colors"
                              :class="i <= pingsRemaining ? 'bg-accent' : 'bg-warm-200'"
                            />
                            <span class="font-display text-[10px] text-muted font-semibold">{{ pingsRemaining }}/3</span>
                          </div>
                        </div>

                        <div class="flex items-center gap-4 mb-3">
                          <div>
                            <p class="font-display font-bold text-2xl tabular-nums text-primary leading-none">{{ pingHistory.length }}</p>
                            <p class="text-[10px] text-muted font-body mt-0.5">total pings</p>
                          </div>
                          <div v-if="lastPing" class="flex-1">
                            <p class="text-[11px] text-secondary font-body leading-relaxed">
                              Last ping <span class="text-primary font-semibold">{{ formatDate(lastPing.created_at || lastPing.pinged_at) }}</span>
                            </p>
                            <div class="flex flex-wrap gap-x-2 gap-y-1 mt-1">
                              <span v-for="(ping, idx) in recentPings" :key="idx" class="inline-flex items-center gap-1 text-[10px] font-body text-secondary">
                                <span class="w-1.5 h-1.5 rounded-full shrink-0"
                                  :class="ping.status_code >= 200 && ping.status_code < 400 ? 'bg-score-good' : 'bg-score-bad'"
                                ></span>
                                {{ ping.ping_type }}
                              </span>
                            </div>
                          </div>
                          <p v-else class="text-xs text-muted font-body flex-1">No pings yet.</p>
                        </div>

                        <button
                          @click="handlePing"
                          :disabled="pinging || pingsRemaining <= 0"
                          class="inline-flex items-center gap-1.5 text-xs font-display font-semibold text-accent hover:text-accent-hover transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                        >
                          <svg v-if="pinging" class="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24">
                            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                          </svg>
                          <svg v-else class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M5.636 18.364a9 9 0 010-12.728m12.728 0a9 9 0 010 12.728M12 12v.01" />
                          </svg>
                          {{ pinging ? 'Pinging…' : pingsRemaining <= 0 ? 'Limit reached today' : 'Ping crawlers now' }}
                        </button>
                      </div>

                    </div>
                  </template>

                  <!-- Non-Pro: locked state with CTA -->
                  <template v-else>
                    <div class="flex flex-col sm:flex-row items-start sm:items-center gap-5 py-1">
                      <div class="flex-1">
                        <p class="font-display font-bold text-base text-primary mb-1.5">Make yourself visible to every AI crawler</p>
                        <p class="text-sm text-secondary font-body leading-relaxed max-w-prose">
                          Host llms.txt, ai.txt, and robots.txt additions directly from AgentCheck. One click — AI agents start indexing you immediately.
                        </p>
                      </div>
                      <router-link to="/pricing" class="btn-primary text-sm px-6 py-3 rounded-xl shrink-0 gap-2">
                        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                          <path stroke-linecap="round" stroke-linejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
                        </svg>
                        Activate AI Presence
                      </router-link>
                    </div>
                  </template>
                </div>
              </div>
            </section>

            <!-- ============================================================ -->
            <!-- 4. AGENT SIMULATOR (Pro)                                      -->
            <!-- ============================================================ -->
            <section v-if="isPro" class="mb-6 animate-slide-up" style="animation-delay: 140ms">
              <!-- Terminal-style panel -->
              <div class="rounded-2xl bg-warm-50 border border-border overflow-hidden">
                <!-- Chrome bar -->
                <div class="flex items-center justify-between px-5 sm:px-6 py-3.5 border-b border-border bg-surface">
                  <div class="flex items-center gap-3">
                    <div class="flex gap-1.5" aria-hidden="true">
                      <span class="w-2.5 h-2.5 rounded-full bg-warm-200"></span>
                      <span class="w-2.5 h-2.5 rounded-full bg-warm-200"></span>
                      <span class="w-2.5 h-2.5 rounded-full bg-warm-200"></span>
                    </div>
                    <p class="font-display font-semibold text-sm text-primary">
                      AI Agent — {{ primaryDomain || 'your site' }}
                    </p>
                    <span class="text-[10px] font-display font-bold uppercase tracking-wider text-accent bg-accent/10 px-2 py-0.5 rounded-md">Pro</span>
                  </div>
                  <template v-if="simulation?.steps">
                    <div class="flex items-center gap-2">
                      <span
                        class="w-1.5 h-1.5 rounded-full animate-pulse shrink-0"
                        :class="simulationRate >= 70 ? 'bg-score-good' : simulationRate >= 40 ? 'bg-score-medium' : 'bg-score-bad'"
                      ></span>
                      <span class="text-xs font-display font-bold tabular-nums" :class="scoreColorClass(simulationRate)">{{ simulationRate }}% success</span>
                    </div>
                  </template>
                  <template v-else>
                    <p class="font-display text-xs text-secondary">Watch how ChatGPT navigates your site</p>
                  </template>
                </div>

                <!-- Body -->
                <div class="px-5 sm:px-6 py-5 sm:py-6">
                  <template v-if="simulation?.steps">
                    <div class="mb-5">
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
                    <div class="sm:columns-2 sm:gap-x-10">
                      <StepFlow :steps="simulation.steps" />
                    </div>
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
                        <p class="font-display font-bold text-base text-primary mb-1.5">See exactly what ChatGPT sees when it visits your site</p>
                        <p class="text-sm text-secondary font-body leading-relaxed max-w-prose">
                          Step-by-step simulation of how AI agents navigate, parse, and understand every page — with pass/fail results for each action.
                        </p>
                      </div>
                      <button
                        @click="handleSimulate"
                        :disabled="simulating || !latestCompletedScan"
                        class="btn-primary text-sm px-6 py-3 rounded-xl disabled:opacity-50 shrink-0 min-h-[44px] gap-2"
                      >
                        <svg v-if="simulating" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                        </svg>
                        <svg v-else class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                          <path stroke-linecap="round" stroke-linejoin="round" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" /><path stroke-linecap="round" stroke-linejoin="round" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        {{ simulating ? 'Running simulation...' : 'Run simulation' }}
                      </button>
                    </div>
                  </template>
                </div>
              </div>
            </section>

            <!-- ============================================================ -->
            <!-- 5. TRACKING — Mentions + Monitors (Pro, compact)             -->
            <!-- ============================================================ -->
            <section v-if="isPro" class="mb-6 animate-slide-up" style="animation-delay: 180ms">
              <div class="flex items-baseline justify-between mb-3">
                <h2 class="font-display text-xs font-bold uppercase tracking-widest text-muted">Tracking</h2>
                <span class="text-[10px] font-display font-bold uppercase tracking-wider text-accent bg-accent/10 px-2 py-0.5 rounded-md">Pro</span>
              </div>

              <div class="grid sm:grid-cols-2 gap-4">

                <!-- AI Mentions widget -->
                <div class="border border-border rounded-xl p-4 sm:p-5 bg-surface">
                  <div class="flex items-start justify-between mb-4">
                    <div>
                      <p class="font-display font-bold text-sm text-primary mb-0.5">AI Mentions</p>
                      <p class="text-xs text-secondary font-body">How often AI models recommend you</p>
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
                    <div class="mb-3">
                      <MentionChart :data="mentions" />
                    </div>
                    <div class="flex items-center justify-between pt-3 border-t border-border-light">
                      <p class="text-xs text-secondary font-body">8-week trend</p>
                      <span v-if="mentionTrend > 0" class="inline-flex items-center gap-1 text-xs text-score-good font-display font-semibold">
                        <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M5 15l7-7 7 7" /></svg>
                        +{{ mentionTrend }} vs last week
                      </span>
                      <span v-else-if="mentionTrend < 0" class="inline-flex items-center gap-1 text-xs text-score-bad font-display font-semibold">
                        <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" /></svg>
                        {{ mentionTrend }} vs last week
                      </span>
                      <span v-else class="text-xs text-muted font-display">Stable</span>
                    </div>
                  </template>

                  <template v-else>
                    <div class="flex flex-col gap-3 py-1">
                      <p class="text-sm text-secondary font-body leading-relaxed">
                        Track how often ChatGPT, Claude, and Gemini mention your site.
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

                <!-- Monitors widget -->
                <div class="border border-border rounded-xl p-4 sm:p-5 bg-surface flex flex-col">
                  <div class="flex items-start justify-between mb-4">
                    <div>
                      <p class="font-display font-bold text-sm text-primary mb-0.5">Monitors</p>
                      <p class="text-xs text-secondary font-body">Active uptime &amp; change detection</p>
                    </div>
                    <div v-if="monitors.length > 0" class="shrink-0 ml-4 text-right">
                      <p class="font-display font-bold text-2xl tabular-nums text-primary leading-none">{{ monitors.length }}</p>
                      <p class="text-[10px] text-muted font-body mt-0.5">active</p>
                    </div>
                  </div>

                  <template v-if="monitors.length > 0">
                    <div class="flex-1 space-y-2">
                      <div
                        v-for="(mon, idx) in monitors.slice(0, 3)"
                        :key="mon.id || idx"
                        class="flex items-center gap-2.5 py-2 border-b border-border-light last:border-0"
                      >
                        <span class="w-1.5 h-1.5 rounded-full bg-score-good animate-pulse-subtle shrink-0"></span>
                        <span class="font-body text-xs text-primary truncate flex-1">{{ mon.domain || mon.url || 'Monitor' }}</span>
                        <span class="text-[10px] font-display font-semibold text-score-good uppercase tracking-wider">Active</span>
                      </div>
                    </div>
                    <p v-if="monitors.length > 3" class="text-xs text-muted font-body mt-3">+{{ monitors.length - 3 }} more monitors</p>
                  </template>

                  <template v-else>
                    <div class="flex-1 flex flex-col justify-between gap-4 py-1">
                      <p class="text-sm text-secondary font-body leading-relaxed">
                        Get alerted when your AI visibility score changes or bots start getting blocked.
                      </p>
                      <router-link
                        to="/monitoring"
                        class="inline-flex items-center gap-1.5 text-xs font-display font-semibold text-accent hover:text-accent-hover transition-colors w-fit"
                      >
                        Set up monitoring
                        <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                          <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
                        </svg>
                      </router-link>
                    </div>
                  </template>
                </div>

              </div>
            </section>

            <!-- ============================================================ -->
            <!-- FREE USER: Pro upsell                                        -->
            <!-- ============================================================ -->
            <template v-if="!isPro && completedScans.length > 0">
              <section class="mb-6 animate-slide-up" style="animation-delay: 140ms">
                <div class="relative rounded-2xl border border-border overflow-hidden">
                  <!-- Blurred preview -->
                  <div class="p-5 sm:p-6 opacity-50 blur-[3px] pointer-events-none select-none" aria-hidden="true">
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
                        <div class="w-full h-1 rounded-full bg-warm-200"><div class="h-full w-4/5 rounded-full bg-score-good"></div></div>
                        <div class="flex items-center gap-3">
                          <span class="w-5 h-5 rounded-full bg-score-good flex items-center justify-center shrink-0"><svg class="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" /></svg></span>
                          <span class="text-sm text-primary font-body">Fetched llms.txt successfully</span>
                        </div>
                        <div class="flex items-center gap-3">
                          <span class="w-5 h-5 rounded-full bg-score-bad flex items-center justify-center shrink-0"><svg class="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" /></svg></span>
                          <span class="text-sm text-score-bad font-body">No contact/about page found for attribution</span>
                        </div>
                      </div>
                    </div>
                    <div class="grid sm:grid-cols-2 gap-4">
                      <div class="border border-border rounded-xl p-4 bg-surface">
                        <p class="font-display font-bold text-sm text-primary mb-1">AI Mentions</p>
                        <p class="text-xs text-secondary font-body mb-3">Mentioned in 7/12 AI queries</p>
                        <div class="flex items-end gap-1 h-10">
                          <div v-for="h in [30, 45, 60, 55, 75, 80, 90, 100]" :key="h" class="flex-1 rounded-t bg-score-good" :style="`height:${h}%`"></div>
                        </div>
                      </div>
                      <div class="border border-border rounded-xl p-4 bg-surface">
                        <p class="font-display font-bold text-sm text-primary mb-3">Crawler Pings</p>
                        <div class="space-y-1.5">
                          <div class="flex items-center gap-2.5 px-2.5 py-2 rounded-lg bg-score-good/5 border border-score-good/10">
                            <span class="w-1.5 h-1.5 rounded-full bg-score-good animate-pulse"></span>
                            <span class="text-xs text-primary font-body">GoogleBot indexed</span>
                            <span class="ml-auto text-[10px] text-score-good font-display font-bold">200</span>
                          </div>
                          <div class="flex items-center gap-2.5 px-2.5 py-2 rounded-lg bg-score-good/5 border border-score-good/10">
                            <span class="w-1.5 h-1.5 rounded-full bg-score-good animate-pulse"></span>
                            <span class="text-xs text-primary font-body">GPTBot notified</span>
                            <span class="ml-auto text-[10px] text-score-good font-display font-bold">200</span>
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
                      <p class="font-display text-xl font-bold text-primary mb-2">Get found by ChatGPT, Claude &amp; Perplexity</p>
                      <p class="text-sm text-secondary font-body leading-relaxed mb-6">
                        Activate AI files, ping crawlers, simulate agent navigation, and track every mention — all in one dashboard.
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

          </template>
          <!-- END HAS SCANS -->

          <!-- ============================================================ -->
          <!-- RECENT SCANS                                                 -->
          <!-- ============================================================ -->
          <section class="mb-10 animate-slide-up" :style="{ animationDelay: isPro ? '220ms' : '160ms' }">
            <div class="flex items-center justify-between mb-3">
              <h2 class="font-display text-xs font-bold uppercase tracking-widest text-muted">Scan History</h2>
              <router-link
                v-if="scans.length > 5"
                to="/history"
                class="inline-flex items-center gap-1 text-xs font-display font-semibold text-accent hover:text-accent-hover transition-colors"
              >
                View all {{ scans.length }}
                <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
                </svg>
              </router-link>
            </div>

            <div v-if="scans.length === 0" class="rounded-xl border border-dashed border-border py-10 text-center bg-surface/50">
              <p class="text-sm text-muted font-body">No scans yet. Run your first scan above.</p>
            </div>

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
                >
                  <span class="absolute left-0 top-0 bottom-0 w-0.5 bg-accent scale-y-0 group-hover:scale-y-100 transition-transform duration-200 origin-center rounded-r-full" />

                  <div class="flex items-center gap-3 min-w-0 flex-1">
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
                      <p class="sm:hidden text-[11px] text-warm-400 font-body mt-0.5 leading-none">
                        <span v-if="scan.created_at">{{ formatDate(scan.created_at) }}</span>
                        <span v-if="scan.status === 'running' || scan.status === 'pending'" class="text-accent">Scanning...</span>
                      </p>
                    </div>
                    <span
                      v-if="scan.site_type"
                      class="hidden sm:inline text-[10px] font-display font-medium uppercase tracking-wider text-warm-500 bg-warm-100 px-1.5 py-0.5 rounded-md shrink-0"
                    >{{ scan.site_type }}</span>
                  </div>

                  <!-- Score -->
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

                  <!-- Date -->
                  <div class="hidden sm:block shrink-0 w-20 text-right">
                    <span v-if="scan.created_at" class="text-xs text-warm-400 font-body tabular-nums">{{ formatDate(scan.created_at) }}</span>
                    <span v-else class="text-xs text-accent font-display animate-pulse">Running...</span>
                  </div>

                  <!-- Delete -->
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

              <!-- Footer -->
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

        </template>
        <!-- END v-else (not loading) -->

      </div>
    </div>
  </AppLayout>
</template>
