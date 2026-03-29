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
  getMentions, getCompetitors, discoverCompetitors,
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
    <div class="flex-1 pb-16 sm:pb-0 bg-page">
      <div class="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-10">

        <!-- ============================================================ -->
        <!-- SCAN BAR                                                      -->
        <!-- ============================================================ -->
        <section class="mb-10 animate-fade-in">
          <form @submit.prevent="handleScan" class="relative flex items-center gap-3">
            <div class="relative flex-1">
              <!-- Search icon inside input -->
              <div class="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-4">
                <svg class="w-4.5 h-4.5 text-warm-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
              <input
                v-model="scanDomain"
                type="text"
                placeholder="Enter any website to scan..."
                class="w-full rounded-lg border border-border bg-surface pl-11 pr-4 py-3.5 text-sm text-primary placeholder:text-warm-400 focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent transition-all"
              />
            </div>
            <button
              type="submit"
              class="btn-primary text-sm px-7 py-3.5 rounded-lg shrink-0"
              :disabled="scanning || !scanDomain.trim()"
            >
              <svg v-if="scanning" class="w-4 h-4 animate-spin mr-2 inline" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" /><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>
              {{ scanning ? 'Scanning...' : 'Run scan' }}
            </button>
          </form>
          <p v-if="error" class="text-sm text-score-bad mt-3 pl-1">{{ error }}</p>
        </section>

        <!-- ============================================================ -->
        <!-- LOADING STATE                                                 -->
        <!-- ============================================================ -->
        <div v-if="loadingScans" class="py-20 text-center">
          <svg class="w-6 h-6 text-accent animate-spin mx-auto mb-3" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          <p class="text-sm text-muted font-body">Loading your dashboard...</p>
        </div>

        <template v-else>

          <!-- ============================================================ -->
          <!-- HERO SECTION                                                 -->
          <!-- ============================================================ -->
          <section v-if="completedScans.length > 0" class="mb-10 animate-slide-up">
            <div class="grid sm:grid-cols-5 gap-5">

              <!-- Left: Score Hero (3 cols) -->
              <div class="sm:col-span-3 border border-border rounded-xl p-6 sm:p-8 bg-surface shadow-sm">
                <div class="flex items-center gap-6 sm:gap-8">
                  <ScoreCircle :score="bestScan.score" :grade="bestScan.grade" :size="160" />
                  <div class="flex-1 min-w-0">
                    <p class="font-display font-semibold text-xs uppercase tracking-wider text-muted mb-2">AI Visibility Score</p>
                    <p class="font-display text-4xl sm:text-5xl font-bold tabular-nums leading-none" :class="scoreColorClass(bestScan.score)">
                      {{ bestScan.score }}<span class="text-lg text-muted font-normal">/100</span>
                    </p>
                    <div class="flex items-center gap-2 mt-3 flex-wrap">
                      <span class="font-display font-bold text-sm px-2.5 py-1 rounded-lg"
                        :class="{
                          'bg-score-good/10 text-score-good': bestScan.score >= 70,
                          'bg-score-medium/10 text-score-medium': bestScan.score >= 40 && bestScan.score < 70,
                          'bg-score-bad/10 text-score-bad': bestScan.score < 40,
                        }">
                        Grade {{ bestScan.grade }}
                      </span>
                      <span v-if="primaryDomain" class="text-sm text-secondary font-body truncate">{{ primaryDomain }}</span>
                      <span v-if="siteTypeLabel" class="text-[10px] font-display font-medium uppercase tracking-wider text-warm-500 bg-warm-100 px-2 py-0.5 rounded-md">{{ siteTypeLabel }}</span>
                    </div>
                    <p class="text-sm text-secondary font-body mt-3 leading-relaxed">{{ scoreMessage }}</p>
                    <!-- Mention summary inline -->
                    <p v-if="isPro && mentionFoundCount > 0" class="text-xs text-accent font-display font-medium mt-3 flex items-center gap-1.5">
                      <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
                      Mentioned in {{ mentionFoundCount }}/{{ mentionTestedCount }} AI queries this week
                    </p>
                  </div>
                </div>
              </div>

              <!-- Right: AI Mention Trend (2 cols) -->
              <div v-if="isPro && mentions.length > 0" class="sm:col-span-2 border border-border rounded-xl p-6 bg-surface shadow-sm flex flex-col">
                <div class="flex items-center justify-between mb-4">
                  <div class="flex items-center gap-2">
                    <div class="w-8 h-8 rounded-lg bg-accent/10 flex items-center justify-center">
                      <svg class="w-4 h-4 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" /></svg>
                    </div>
                    <p class="font-display font-semibold text-sm text-primary">AI Mentions</p>
                  </div>
                  <span class="text-[10px] font-display font-bold uppercase tracking-wider text-accent bg-accent/10 px-2 py-0.5 rounded-md">Pro</span>
                </div>
                <div class="flex-1 flex flex-col justify-center">
                  <MentionChart :data="mentions" />
                </div>
                <div class="flex items-center justify-between mt-4 pt-3 border-t border-border-light">
                  <p class="text-xs text-secondary font-body">
                    {{ mentionFoundCount }}/{{ mentionTestedCount }} queries
                  </p>
                  <span v-if="mentionTrend > 0" class="inline-flex items-center gap-1 text-xs text-score-good font-display font-semibold bg-score-good/8 px-2 py-0.5 rounded-md">
                    <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M5 15l7-7 7 7" /></svg>
                    +{{ mentionTrend }}
                  </span>
                  <span v-else-if="mentionTrend < 0" class="inline-flex items-center gap-1 text-xs text-score-bad font-display font-semibold bg-score-bad/8 px-2 py-0.5 rounded-md">
                    <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" /></svg>
                    {{ mentionTrend }}
                  </span>
                  <span v-else class="text-xs text-muted font-display font-medium">No change</span>
                </div>
              </div>

              <!-- Right fallback: no mentions or free -->
              <div v-else class="sm:col-span-2 border border-border rounded-xl p-6 bg-surface shadow-sm flex flex-col justify-center">
                <div class="flex items-center gap-2 mb-4">
                  <div class="w-8 h-8 rounded-lg bg-warm-100 flex items-center justify-center">
                    <svg class="w-4 h-4 text-warm-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" /></svg>
                  </div>
                  <p class="font-display font-semibold text-sm text-primary">AI Mentions</p>
                </div>
                <p class="text-sm text-secondary font-body leading-relaxed">
                  <template v-if="!isPro">Upgrade to Pro to track how often AI agents mention your site in their responses.</template>
                  <template v-else>Run a mention scan to see how often AI agents reference your domain across queries.</template>
                </p>
                <div v-if="!isPro" class="mt-4">
                  <router-link to="/pricing" class="inline-flex items-center gap-1.5 text-xs font-display font-semibold text-accent hover:text-accent-hover transition-colors">
                    Learn more
                    <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" /></svg>
                  </router-link>
                </div>
              </div>
            </div>
          </section>

          <!-- No scans yet -->
          <section v-else class="mb-10 animate-slide-up">
            <div class="border-2 border-dashed border-border rounded-2xl p-12 sm:p-16 text-center bg-surface/50">
              <div class="w-16 h-16 rounded-2xl bg-accent/10 flex items-center justify-center mx-auto mb-5">
                <svg class="w-8 h-8 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
              </div>
              <p class="font-display text-xl font-bold text-primary mb-2">No scans yet</p>
              <p class="text-sm text-secondary font-body max-w-sm mx-auto">Enter a domain above to run your first scan and discover how AI agents see your site.</p>
            </div>
          </section>

          <!-- ============================================================ -->
          <!-- PRO WIDGETS                                                  -->
          <!-- ============================================================ -->
          <template v-if="isPro">

            <!-- ---- SECTION: Automation ---- -->
            <section class="mb-10 animate-slide-up" style="animation-delay: 60ms">
              <h2 class="font-display text-sm font-bold uppercase tracking-wider text-muted mb-5">Automation</h2>
              <div class="grid sm:grid-cols-2 gap-5">

                <!-- ---- Hosted Files Card ---- -->
                <div class="border border-border rounded-xl p-5 bg-surface">
                  <div class="flex items-center justify-between mb-4">
                    <div class="flex items-center gap-2.5">
                      <div class="w-8 h-8 rounded-lg bg-accent/10 flex items-center justify-center">
                        <svg class="w-4 h-4 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
                      </div>
                      <p class="font-display font-semibold text-sm text-primary">Hosted Files</p>
                    </div>
                  </div>

                  <template v-if="filesActive">
                    <div class="space-y-2.5">
                      <div
                        v-for="file in hostedFiles"
                        :key="file.id || file.file_type"
                        class="flex items-center gap-3 p-3 rounded-xl bg-warm-50 border border-border-light"
                      >
                        <div class="w-7 h-7 rounded-lg bg-score-good/10 flex items-center justify-center shrink-0">
                          <svg class="w-3.5 h-3.5 text-score-good" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" /></svg>
                        </div>
                        <div class="min-w-0 flex-1">
                          <p class="text-xs font-display font-semibold text-primary">{{ file.file_type }}</p>
                          <p class="text-[11px] text-muted truncate font-body">{{ hostedUrl(file) }}</p>
                        </div>
                        <button
                          @click.prevent="copyToClipboard(hostedUrl(file))"
                          class="shrink-0 inline-flex items-center gap-1 text-xs font-display font-medium px-2.5 py-1.5 rounded-lg transition-all"
                          :class="copiedUrl === hostedUrl(file) ? 'bg-score-good/10 text-score-good' : 'bg-warm-100 text-secondary hover:bg-accent/10 hover:text-accent'"
                        >
                          <svg v-if="copiedUrl === hostedUrl(file)" class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" /></svg>
                          <svg v-else class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>
                          {{ copiedUrl === hostedUrl(file) ? 'Copied' : 'Copy' }}
                        </button>
                      </div>
                    </div>
                    <div class="mt-4 pt-3 border-t border-border-light">
                      <p class="text-[11px] text-muted font-body flex items-center gap-1.5">
                        <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                        <template v-if="hostedFiles[0]?.updated_at">Last updated {{ formatDate(hostedFiles[0].updated_at) }}</template>
                        <template v-else>Active and serving</template>
                      </p>
                      <p class="text-[11px] text-secondary font-body mt-1.5">Add a redirect from your domain's <code class="bg-warm-100 px-1 rounded text-[10px]">/.well-known/</code> to these hosted URLs.</p>
                    </div>
                  </template>

                  <template v-else>
                    <p class="text-sm text-secondary font-body mb-4 leading-relaxed">
                      Generate and host AI-ready files like <strong class="font-semibold text-primary">llms.txt</strong> and <strong class="font-semibold text-primary">robots.txt</strong> directives on your domain.
                    </p>
                    <button
                      @click="handleActivateFiles"
                      :disabled="activatingFiles || !primaryDomain"
                      class="btn-primary text-sm px-5 py-2.5 rounded-lg disabled:opacity-50"
                    >
                      <svg v-if="activatingFiles" class="w-4 h-4 animate-spin inline mr-2" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" /><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>
                      {{ activatingFiles ? 'Activating...' : 'Activate AI Files' }}
                    </button>
                  </template>
                </div>

                <!-- ---- Crawler Status Card ---- -->
                <div class="border border-border rounded-xl p-5 bg-surface">
                  <div class="flex items-center justify-between mb-4">
                    <div class="flex items-center gap-2.5">
                      <div class="w-8 h-8 rounded-lg bg-accent/10 flex items-center justify-center">
                        <svg class="w-4 h-4 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M8.111 16.404a5.5 5.5 0 017.778 0M12 20h.01m-7.08-7.071c3.904-3.905 10.236-3.905 14.14 0M1.394 9.393c5.857-5.858 15.355-5.858 21.213 0" /></svg>
                      </div>
                      <p class="font-display font-semibold text-sm text-primary">Crawler Status</p>
                    </div>
                    <button
                      @click="handlePing"
                      :disabled="pinging || pingsRemaining <= 0"
                      class="inline-flex items-center gap-1.5 text-xs font-display font-semibold px-3.5 py-2 rounded-lg bg-accent/10 text-accent hover:bg-accent/15 transition-all disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                      <svg v-if="pinging" class="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" /><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>
                      <svg v-else class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M5.636 18.364a9 9 0 010-12.728m12.728 0a9 9 0 010 12.728M12 12v.01" /></svg>
                      {{ pinging ? 'Pinging...' : 'Ping now' }}
                    </button>
                  </div>

                  <!-- Big stat -->
                  <div class="mb-4">
                    <p class="font-display text-3xl font-bold tabular-nums text-primary">{{ pingHistory.length }}</p>
                    <p class="text-xs text-muted font-body mt-0.5">crawlers pinged total</p>
                  </div>

                  <!-- Remaining pings -->
                  <div class="flex items-center gap-2 mb-4 p-2.5 rounded-lg bg-warm-50 border border-border-light">
                    <div class="flex gap-1">
                      <span v-for="i in 3" :key="i" class="w-2 h-2 rounded-full" :class="i <= pingsRemaining ? 'bg-accent' : 'bg-warm-200'" />
                    </div>
                    <p class="text-xs text-secondary font-body">{{ pingsRemaining }} of 3 remaining today</p>
                  </div>

                  <!-- Last ping info -->
                  <div v-if="lastPing" class="mb-4">
                    <p class="text-xs text-secondary font-body">
                      Last ping: {{ formatDate(lastPing.created_at || lastPing.pinged_at) }} at {{ formatTime(lastPing.created_at || lastPing.pinged_at) }}
                    </p>
                  </div>
                  <p v-else class="text-xs text-muted font-body mb-4">No pings sent yet. Notify crawlers to re-index your site.</p>

                  <!-- Recent ping log -->
                  <div v-if="recentPings.length > 0" class="space-y-1.5">
                    <div
                      v-for="(ping, idx) in recentPings"
                      :key="idx"
                      class="flex items-center gap-2.5 text-xs py-1.5"
                    >
                      <span class="w-2 h-2 rounded-full shrink-0"
                        :class="ping.status_code >= 200 && ping.status_code < 400 ? 'bg-score-good' : 'bg-score-bad'" />
                      <span class="text-secondary font-display font-medium">{{ ping.ping_type }}</span>
                      <span class="text-muted font-body truncate flex-1">{{ ping.target_url?.replace('https://', '').slice(0, 40) }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            <!-- ---- SECTION: Intelligence ---- -->
            <section class="mb-10 animate-slide-up" style="animation-delay: 120ms">
              <h2 class="font-display text-sm font-bold uppercase tracking-wider text-muted mb-5">Intelligence</h2>
              <div class="grid sm:grid-cols-2 gap-5">

                <!-- ---- Competitor Tracking Card ---- -->
                <div class="border border-border rounded-xl p-5 bg-surface">
                  <div class="flex items-center justify-between mb-4">
                    <div class="flex items-center gap-2.5">
                      <div class="w-8 h-8 rounded-lg bg-accent/10 flex items-center justify-center">
                        <svg class="w-4 h-4 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7" /></svg>
                      </div>
                      <p class="font-display font-semibold text-sm text-primary">Competitors</p>
                    </div>
                    <template v-if="competitors.length > 0">
                      <router-link
                        :to="{ path: '/compare' }"
                        class="inline-flex items-center gap-1 text-xs text-accent hover:text-accent-hover font-display font-semibold transition-colors"
                      >
                        Compare all
                        <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" /></svg>
                      </router-link>
                    </template>
                  </div>

                  <template v-if="shownCompetitors.length > 0">
                    <!-- Your domain at top -->
                    <div v-if="bestScan" class="flex items-center justify-between p-3 rounded-xl bg-accent/5 border border-accent/15 mb-2.5">
                      <div class="flex items-center gap-2.5">
                        <div class="w-6 h-6 rounded-md bg-accent/15 flex items-center justify-center">
                          <svg class="w-3 h-3 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" /></svg>
                        </div>
                        <span class="text-xs font-display font-bold text-accent truncate">{{ primaryDomain }}</span>
                      </div>
                      <span class="text-sm font-display font-bold tabular-nums" :class="scoreColorClass(bestScan.score)">{{ bestScan.score }}</span>
                    </div>
                    <!-- Competitor rows -->
                    <div class="space-y-1">
                      <div
                        v-for="(comp, idx) in shownCompetitors"
                        :key="comp.competitor_domain || comp.domain"
                        class="flex items-center justify-between p-3 rounded-xl hover:bg-warm-50 transition-colors"
                      >
                        <div class="flex items-center gap-2.5">
                          <span class="w-6 h-6 rounded-md bg-warm-100 flex items-center justify-center text-[10px] font-display font-bold text-warm-500">{{ idx + 1 }}</span>
                          <span class="text-xs font-display font-medium text-primary truncate">{{ comp.competitor_domain || comp.domain }}</span>
                        </div>
                        <span
                          class="text-sm font-display font-bold tabular-nums"
                          :class="scoreColorClass(comp.last_score ?? comp.score)"
                        >
                          {{ comp.last_score ?? comp.score ?? '--' }}
                        </span>
                      </div>
                    </div>
                    <p v-if="competitors.length > 5" class="text-xs text-muted font-body mt-3 text-center">
                      + {{ competitors.length - 5 }} more competitors tracked
                    </p>
                  </template>

                  <template v-else>
                    <p class="text-sm text-secondary font-body mb-4 leading-relaxed">
                      Find and track competitors in your space to compare AI visibility scores side by side.
                    </p>
                    <button
                      @click="handleDiscoverCompetitors"
                      :disabled="discoveringComps || !primaryDomain"
                      class="btn-primary text-sm px-5 py-2.5 rounded-lg disabled:opacity-50"
                    >
                      <svg v-if="discoveringComps" class="w-4 h-4 animate-spin inline mr-2" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" /><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>
                      {{ discoveringComps ? 'Discovering...' : 'Discover competitors' }}
                    </button>
                  </template>
                </div>

                <!-- ---- Content Suggestions Card ---- -->
                <div class="border border-border rounded-xl p-5 bg-surface">
                  <div class="flex items-center justify-between mb-4">
                    <div class="flex items-center gap-2.5">
                      <div class="w-8 h-8 rounded-lg bg-accent/10 flex items-center justify-center">
                        <svg class="w-4 h-4 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" /></svg>
                      </div>
                      <p class="font-display font-semibold text-sm text-primary">Content Suggestions</p>
                    </div>
                    <template v-if="suggestionCount > 0">
                      <span class="text-[10px] font-display font-bold bg-accent text-white px-2 py-0.5 rounded-full tabular-nums">{{ suggestionCount }}</span>
                    </template>
                  </div>

                  <template v-if="suggestionCount > 0">
                    <p class="text-sm text-secondary font-body mb-4">
                      {{ suggestionCount }} improvement{{ suggestionCount > 1 ? 's' : '' }} found to boost your visibility score.
                    </p>

                    <button
                      @click="suggestionsExpanded = !suggestionsExpanded"
                      class="inline-flex items-center gap-1.5 text-xs font-display font-semibold text-accent hover:text-accent-hover transition-colors mb-1"
                    >
                      <svg class="w-3.5 h-3.5 transition-transform" :class="suggestionsExpanded ? 'rotate-180' : ''" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" /></svg>
                      {{ suggestionsExpanded ? 'Collapse' : 'View suggestions' }}
                    </button>

                    <div v-if="suggestionsExpanded" class="divide-y divide-border-light mt-4">
                      <div
                        v-for="(sugg, idx) in contentSuggs.suggestions"
                        :key="idx"
                        class="py-4 first:pt-0 last:pb-0"
                      >
                        <div class="flex items-start justify-between gap-2 mb-2">
                          <p class="text-sm font-display font-semibold text-primary">{{ sugg.element || sugg.title || `Suggestion ${idx + 1}` }}</p>
                          <span class="text-[10px] font-display font-bold uppercase tracking-wider text-warm-500 bg-warm-100 px-1.5 py-0.5 rounded shrink-0">#{{ idx + 1 }}</span>
                        </div>
                        <p v-if="sugg.reason" class="text-xs text-muted font-body mb-3 leading-relaxed">{{ sugg.reason }}</p>

                        <div v-if="sugg.current" class="mb-2.5">
                          <p class="text-[10px] text-muted uppercase tracking-wider font-display font-semibold mb-1">Current</p>
                          <p class="text-xs text-secondary font-body bg-score-bad/5 border border-score-bad/10 rounded-lg p-2.5 leading-relaxed">{{ sugg.current }}</p>
                        </div>
                        <div v-if="sugg.suggested">
                          <p class="text-[10px] text-muted uppercase tracking-wider font-display font-semibold mb-1">Suggested</p>
                          <div class="flex items-start gap-2">
                            <p class="text-xs text-primary font-body bg-score-good/5 border border-score-good/10 rounded-lg p-2.5 flex-1 leading-relaxed">{{ sugg.suggested }}</p>
                            <button
                              @click="copyToClipboard(sugg.suggested)"
                              class="shrink-0 mt-1 inline-flex items-center gap-1 text-[11px] font-display font-medium px-2 py-1 rounded-lg transition-all"
                              :class="copiedUrl === sugg.suggested ? 'bg-score-good/10 text-score-good' : 'bg-warm-100 text-secondary hover:bg-accent/10 hover:text-accent'"
                            >
                              <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>
                              {{ copiedUrl === sugg.suggested ? 'Copied' : 'Copy' }}
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>
                  </template>

                  <template v-else>
                    <p class="text-sm text-secondary font-body mb-4 leading-relaxed">
                      Get AI-powered content improvements tailored to your site to boost your visibility score.
                    </p>
                    <button
                      @click="handleOptimize"
                      :disabled="optimizing || !latestCompletedScan"
                      class="btn-primary text-sm px-5 py-2.5 rounded-lg disabled:opacity-50"
                    >
                      <svg v-if="optimizing" class="w-4 h-4 animate-spin inline mr-2" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" /><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>
                      {{ optimizing ? 'Generating...' : 'Generate suggestions' }}
                    </button>
                  </template>
                </div>
              </div>
            </section>

            <!-- ---- SECTION: Activity ---- -->
            <section class="mb-10 animate-slide-up" style="animation-delay: 180ms">
              <h2 class="font-display text-sm font-bold uppercase tracking-wider text-muted mb-5">Activity</h2>

              <!-- ---- Agent Simulator Card (full width) ---- -->
              <div class="border border-border rounded-xl p-5 bg-surface">
                <div class="flex items-center justify-between mb-5">
                  <div class="flex items-center gap-2.5">
                    <div class="w-8 h-8 rounded-lg bg-accent/10 flex items-center justify-center">
                      <svg class="w-4 h-4 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" /></svg>
                    </div>
                    <p class="font-display font-semibold text-sm text-primary">Agent Simulator</p>
                  </div>
                </div>

                <template v-if="simulation?.steps">
                  <!-- Progress bar -->
                  <div class="mb-5">
                    <div class="flex items-center justify-between mb-2">
                      <p class="text-xs text-secondary font-body">Completion rate</p>
                      <p class="text-sm font-display font-bold tabular-nums" :class="scoreColorClass(simulationRate)">{{ simulationRate }}%</p>
                    </div>
                    <div class="w-full h-2.5 rounded-full bg-warm-100 overflow-hidden">
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
                    <div class="flex items-center gap-4 mt-2">
                      <span class="flex items-center gap-1.5 text-[11px] text-muted font-body">
                        <span class="w-2 h-2 rounded-full bg-score-good"></span> Pass
                      </span>
                      <span class="flex items-center gap-1.5 text-[11px] text-muted font-body">
                        <span class="w-2 h-2 rounded-full bg-score-bad"></span> Fail
                      </span>
                      <span class="flex items-center gap-1.5 text-[11px] text-muted font-body">
                        <span class="w-2 h-2 rounded-full bg-warm-200"></span> Blocked
                      </span>
                    </div>
                  </div>
                  <StepFlow :steps="simulation.steps" />
                </template>

                <template v-else>
                  <div class="flex items-center gap-4">
                    <p class="text-sm text-secondary font-body leading-relaxed flex-1">
                      Simulate how an AI agent navigates and understands your site step by step.
                    </p>
                    <button
                      @click="handleSimulate"
                      :disabled="simulating || !latestCompletedScan"
                      class="btn-primary text-sm px-5 py-2.5 rounded-lg disabled:opacity-50 shrink-0"
                    >
                      <svg v-if="simulating" class="w-4 h-4 animate-spin inline mr-2" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" /><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>
                      {{ simulating ? 'Running...' : 'Run simulation' }}
                    </button>
                  </div>
                </template>
              </div>
            </section>

          </template>
          <!-- END PRO WIDGETS -->

          <!-- ============================================================ -->
          <!-- FREE USER: Blurred Pro Preview                               -->
          <!-- ============================================================ -->
          <template v-if="!isPro && completedScans.length > 0">
            <section class="mb-10 animate-slide-up" style="animation-delay: 80ms">
              <div class="relative rounded-2xl border border-border overflow-hidden">
                <!-- Blurred preview content -->
                <div class="grid sm:grid-cols-2 gap-5 p-6 opacity-40 blur-[2px] pointer-events-none select-none" aria-hidden="true">
                  <div class="border border-border rounded-xl p-5 bg-surface h-44"></div>
                  <div class="border border-border rounded-xl p-5 bg-surface h-44"></div>
                  <div class="border border-border rounded-xl p-5 bg-surface h-44"></div>
                  <div class="border border-border rounded-xl p-5 bg-surface h-44"></div>
                </div>
                <!-- Overlay CTA -->
                <div class="absolute inset-0 flex flex-col items-center justify-center bg-surface/60 backdrop-blur-sm">
                  <div class="w-14 h-14 rounded-2xl bg-accent/10 flex items-center justify-center mb-4">
                    <svg class="w-7 h-7 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" /></svg>
                  </div>
                  <p class="font-display text-lg font-bold text-primary mb-1">Unlock Pro features</p>
                  <p class="text-sm text-secondary font-body mb-5 max-w-xs text-center">AI file hosting, crawler pinging, competitor tracking, content suggestions, and agent simulation.</p>
                  <router-link to="/pricing" class="btn-primary text-sm px-6 py-2.5 rounded-xl shadow-sm">
                    Upgrade to Pro
                  </router-link>
                </div>
              </div>
            </section>
          </template>

          <!-- ============================================================ -->
          <!-- RECENT SCANS                                                 -->
          <!-- ============================================================ -->
          <section class="mb-10 animate-slide-up" :style="{ animationDelay: isPro ? '240ms' : '120ms' }">
            <div class="flex items-center justify-between mb-5">
              <h2 class="font-display text-sm font-bold uppercase tracking-wider text-muted">Recent Scans</h2>
              <router-link to="/" class="inline-flex items-center gap-1.5 text-xs text-accent hover:text-accent-hover transition-colors font-display font-semibold px-3 py-1.5 rounded-lg bg-accent/5 hover:bg-accent/10">
                <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4" /></svg>
                New scan
              </router-link>
            </div>

            <div v-if="scans.length === 0" class="border-2 border-dashed border-border rounded-2xl p-12 text-center bg-surface/50">
              <div class="w-12 h-12 rounded-xl bg-warm-100 flex items-center justify-center mx-auto mb-4">
                <svg class="w-6 h-6 text-warm-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" /></svg>
              </div>
              <p class="font-display font-bold text-primary mb-1">No scans yet</p>
              <p class="text-sm text-secondary font-body">Run your first scan above to get started.</p>
            </div>

            <div v-else class="border border-border rounded-xl bg-surface overflow-hidden divide-y divide-border-light">
              <router-link
                v-for="scan in recentScans"
                :key="scan.scan_id"
                :to="scan.status === 'completed' ? { name: 'Report', params: { id: scan.scan_id } } : { name: 'ScanProgress', params: { id: scan.scan_id } }"
                class="relative flex items-center gap-4 px-5 py-4 hover:bg-warm-50 transition-colors group cursor-pointer"
              >
                <!-- Score circle or spinner -->
                <div class="flex-shrink-0 w-12 h-12 flex items-center justify-center">
                  <ScoreCircle v-if="scan.status === 'completed' && scan.score != null" :score="scan.score" :size="48" />
                  <div v-else-if="scan.status === 'pending' || scan.status === 'running'" class="w-11 h-11 rounded-full border-2 border-accent/20 bg-accent/5 flex items-center justify-center">
                    <svg class="w-5 h-5 text-accent animate-spin" fill="none" viewBox="0 0 24 24">
                      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                  </div>
                  <div v-else class="w-11 h-11 rounded-full border-2 border-score-bad/20 bg-score-bad/5 flex items-center justify-center">
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
                      class="text-[10px] font-display font-medium uppercase tracking-wider text-warm-500 bg-warm-100 px-1.5 py-0.5 rounded-md"
                    >
                      {{ scan.site_type }}
                    </span>
                  </div>
                  <p class="text-xs text-muted font-body mt-0.5">
                    <span v-if="scan.created_at">{{ formatDate(scan.created_at) }}</span>
                  </p>
                </div>

                <!-- Grade badge -->
                <div class="flex items-center gap-3 shrink-0">
                  <span
                    v-if="scan.status === 'completed' && scan.score != null"
                    class="text-xs font-display font-bold px-2.5 py-1 rounded-lg"
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
                    class="text-[11px] font-display font-medium text-accent bg-accent/10 px-2 py-1 rounded-lg"
                  >
                    Scanning...
                  </span>

                  <!-- Arrow -->
                  <svg class="w-4 h-4 text-warm-300 group-hover:text-accent transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
                  </svg>
                </div>

                <!-- Delete button -->
                <button
                  @click.prevent.stop="handleDeleteScan(scan.scan_id)"
                  class="absolute right-2 top-2 w-6 h-6 rounded-md flex items-center justify-center text-warm-300 hover:text-score-bad hover:bg-score-bad/10 transition-colors opacity-0 group-hover:opacity-100"
                  title="Delete scan"
                >
                  <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </router-link>
            </div>
          </section>

          <!-- ============================================================ -->
          <!-- UPGRADE CARD (free users, bottom)                            -->
          <!-- ============================================================ -->
          <section v-if="!isPro" class="mb-10 animate-slide-up" style="animation-delay: 160ms">
            <UpgradeCard />
          </section>

        </template>
      </div>
    </div>
  </AppLayout>
</template>
