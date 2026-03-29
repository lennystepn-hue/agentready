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
  getUserScans, getMonitors, startScan,
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
  hostedFiles.value.length > 0 && hostedFiles.value.some(f => f.active || f.url)
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

const shownCompetitors = computed(() => competitors.value.slice(0, 3))

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
    const data = await activateHostedFiles(primaryDomain.value, latestCompletedScan.value.scan_id)
    hostedFiles.value = Array.isArray(data) ? data : (data.files || [data])
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
    const data = await discoverCompetitors(primaryDomain.value)
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

function copyToClipboard(text) {
  navigator.clipboard.writeText(text)
  copiedUrl.value = text
  setTimeout(() => { copiedUrl.value = '' }, 2000)
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
        mentions.value = Array.isArray(d) ? d : (d.mentions || d.weeks || [])
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
    <div class="flex-1 pb-16 sm:pb-0">
      <div class="max-w-5xl mx-auto px-6 lg:px-8 py-8">

        <!-- 1. Scan Bar -->
        <section class="mb-8 animate-fade-in">
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

        <!-- Loading state -->
        <div v-if="loadingScans" class="py-12 text-center">
          <svg class="w-5 h-5 text-accent animate-spin mx-auto mb-2" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          <p class="text-sm text-muted">Loading dashboard...</p>
        </div>

        <template v-else>

          <!-- 2. Hero Row -->
          <section v-if="completedScans.length > 0" class="mb-8 animate-slide-up">
            <div class="grid sm:grid-cols-2 gap-4">
              <!-- Left: Score -->
              <div class="border border-border rounded-lg p-5 bg-surface flex items-center gap-5">
                <ScoreCircle :score="bestScan.score" :grade="bestScan.grade" :size="120" />
                <div>
                  <p class="font-display font-semibold text-sm text-primary">Your AI Visibility</p>
                  <p class="font-display text-3xl font-bold tabular-nums mt-1" :class="scoreColorClass(bestScan.score)">
                    {{ bestScan.score }}
                  </p>
                  <p class="text-xs text-muted mt-1">
                    Grade: <span class="font-display font-semibold" :class="scoreColorClass(bestScan.score)">{{ bestScan.grade }}</span>
                  </p>
                </div>
              </div>

              <!-- Right: AI Mention Trend (Pro) -->
              <div v-if="isPro && mentions.length > 0" class="border border-border rounded-lg p-5 bg-surface">
                <div class="flex items-center justify-between mb-3">
                  <p class="font-display font-semibold text-sm text-primary">AI Mention Trend</p>
                  <span class="text-[10px] font-display font-bold uppercase tracking-wider text-accent bg-accent/10 px-1.5 py-0.5 rounded">Pro</span>
                </div>
                <MentionChart :data="mentions" />
                <div class="flex items-center gap-2 mt-3">
                  <p class="text-xs text-secondary">
                    Found in {{ mentionFoundCount }}/{{ mentionTestedCount }} queries this week
                  </p>
                  <span v-if="mentionTrend > 0" class="text-xs text-score-good font-display font-medium">
                    &#9650; +{{ mentionTrend }}
                  </span>
                  <span v-else-if="mentionTrend < 0" class="text-xs text-score-bad font-display font-medium">
                    &#9660; {{ mentionTrend }}
                  </span>
                  <span v-else class="text-xs text-muted font-display font-medium">
                    &#8212; No change
                  </span>
                </div>
              </div>

              <!-- Right fallback for free users or no mentions -->
              <div v-else class="border border-border rounded-lg p-5 bg-surface flex flex-col justify-center">
                <p class="font-display font-semibold text-sm text-primary mb-1">AI Mention Trend</p>
                <p class="text-xs text-muted">
                  <template v-if="!isPro">Upgrade to Pro to track AI mentions of your site.</template>
                  <template v-else>Run a mention scan to see how often AI agents reference your domain.</template>
                </p>
              </div>
            </div>
          </section>

          <!-- No scans yet -->
          <section v-else class="mb-8 animate-slide-up">
            <div class="border border-dashed border-border rounded-lg p-10 text-center">
              <p class="font-display font-semibold text-primary mb-1">No scans yet</p>
              <p class="text-sm text-secondary mb-5">Run your first scan to see how your site performs with AI agents.</p>
            </div>
          </section>

          <!-- PRO WIDGETS -->
          <template v-if="isPro">

            <!-- 3. Automation Row -->
            <section class="mb-8 animate-slide-up" style="animation-delay: 60ms">
              <div class="grid sm:grid-cols-2 gap-4">

                <!-- Hosted Files Card -->
                <div class="border border-border rounded-lg p-5 bg-surface">
                  <div class="flex items-center justify-between mb-3">
                    <p class="font-display font-semibold text-sm text-primary">Hosted Files</p>
                    <span class="text-[10px] font-display font-bold uppercase tracking-wider text-accent bg-accent/10 px-1.5 py-0.5 rounded">Pro</span>
                  </div>

                  <template v-if="filesActive">
                    <div class="space-y-2">
                      <div
                        v-for="file in hostedFiles"
                        :key="file.filename || file.url"
                        class="flex items-center justify-between gap-2 text-xs"
                      >
                        <div class="min-w-0 flex-1">
                          <p class="font-display font-medium text-primary truncate">{{ file.filename || file.path }}</p>
                          <p class="text-muted truncate">{{ file.url }}</p>
                        </div>
                        <button
                          @click="copyToClipboard(file.url)"
                          class="text-xs text-accent hover:text-accent-hover font-display font-medium shrink-0"
                        >
                          {{ copiedUrl === file.url ? 'Copied!' : 'Copy' }}
                        </button>
                      </div>
                    </div>
                    <p v-if="hostedFiles[0]?.updated_at" class="text-[11px] text-muted mt-3">
                      Last updated: {{ formatDate(hostedFiles[0].updated_at) }}
                    </p>
                  </template>

                  <template v-else>
                    <p class="text-xs text-secondary mb-3">
                      Generate and host AI-ready files (llms.txt, robots.txt directives) on your domain.
                    </p>
                    <button
                      @click="handleActivateFiles"
                      :disabled="activatingFiles || !primaryDomain"
                      class="text-xs text-accent hover:text-accent-hover font-display font-medium disabled:opacity-50"
                    >
                      <template v-if="activatingFiles">
                        <svg class="w-3 h-3 animate-spin inline mr-1" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" /><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>
                        Activating...
                      </template>
                      <template v-else>Activate AI Files</template>
                    </button>
                  </template>
                </div>

                <!-- Crawler Status Card -->
                <div class="border border-border rounded-lg p-5 bg-surface">
                  <div class="flex items-center justify-between mb-3">
                    <p class="font-display font-semibold text-sm text-primary">Crawler Status</p>
                    <button
                      @click="handlePing"
                      :disabled="pinging || pingsRemaining <= 0"
                      class="text-xs text-accent hover:text-accent-hover font-display font-medium disabled:opacity-50"
                    >
                      <template v-if="pinging">
                        <svg class="w-3 h-3 animate-spin inline mr-1" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" /><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>
                        Pinging...
                      </template>
                      <template v-else>Ping now</template>
                    </button>
                  </div>

                  <div v-if="lastPing" class="mb-2">
                    <p class="text-xs text-secondary">
                      Last ping: {{ formatDate(lastPing.created_at || lastPing.pinged_at) }} at {{ formatTime(lastPing.created_at || lastPing.pinged_at) }}
                    </p>
                  </div>
                  <p v-else class="text-xs text-muted mb-2">No pings sent yet.</p>

                  <p class="text-[11px] text-muted mb-3">{{ pingsRemaining }} pings remaining today</p>

                  <div v-if="recentPings.length > 0" class="space-y-1">
                    <div
                      v-for="(ping, idx) in recentPings"
                      :key="idx"
                      class="flex items-center gap-2 text-[11px]"
                    >
                      <span class="w-1.5 h-1.5 rounded-full shrink-0"
                        :class="ping.status === 'success' || ping.accepted ? 'bg-score-good' : 'bg-score-bad'" />
                      <span class="text-muted">{{ formatDate(ping.created_at || ping.pinged_at) }}</span>
                      <span class="text-secondary">{{ ping.crawlers_pinged || ping.count || '' }} crawlers</span>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            <!-- 4. Intelligence Row -->
            <section class="mb-8 animate-slide-up" style="animation-delay: 120ms">
              <div class="grid sm:grid-cols-2 gap-4">

                <!-- Competitor Tracking Card -->
                <div class="border border-border rounded-lg p-5 bg-surface">
                  <div class="flex items-center justify-between mb-3">
                    <p class="font-display font-semibold text-sm text-primary">Competitor Tracking</p>
                    <template v-if="competitors.length > 0">
                      <router-link
                        :to="{ path: '/compare' }"
                        class="text-xs text-accent hover:text-accent-hover font-display font-medium"
                      >
                        Scan all
                      </router-link>
                    </template>
                  </div>

                  <template v-if="shownCompetitors.length > 0">
                    <div class="space-y-2">
                      <div
                        v-for="comp in shownCompetitors"
                        :key="comp.domain"
                        class="flex items-center justify-between text-xs"
                      >
                        <span class="font-display font-medium text-primary truncate">{{ comp.domain }}</span>
                        <span
                          class="font-display font-bold tabular-nums"
                          :class="scoreColorClass(comp.score ?? comp.last_score)"
                        >
                          {{ comp.score ?? comp.last_score ?? '—' }}
                        </span>
                      </div>
                    </div>
                    <p v-if="competitors.length > 3" class="text-[11px] text-muted mt-2">
                      + {{ competitors.length - 3 }} more
                    </p>
                  </template>

                  <template v-else>
                    <p class="text-xs text-secondary mb-3">
                      Find and track competitors in your space to compare AI visibility.
                    </p>
                    <button
                      @click="handleDiscoverCompetitors"
                      :disabled="discoveringComps || !primaryDomain"
                      class="text-xs text-accent hover:text-accent-hover font-display font-medium disabled:opacity-50"
                    >
                      <template v-if="discoveringComps">
                        <svg class="w-3 h-3 animate-spin inline mr-1" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" /><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>
                        Discovering...
                      </template>
                      <template v-else>Discover competitors</template>
                    </button>
                  </template>
                </div>

                <!-- Content Suggestions Card -->
                <div class="border border-border rounded-lg p-5 bg-surface">
                  <div class="flex items-center justify-between mb-3">
                    <p class="font-display font-semibold text-sm text-primary">Content Suggestions</p>
                    <template v-if="contentSuggs?.suggestions?.length > 0">
                      <button
                        @click="suggestionsExpanded = !suggestionsExpanded"
                        class="text-xs text-accent hover:text-accent-hover font-display font-medium"
                      >
                        {{ suggestionsExpanded ? 'Collapse' : 'View suggestions' }}
                      </button>
                    </template>
                  </div>

                  <template v-if="contentSuggs?.suggestions?.length > 0">
                    <p class="text-xs text-secondary mb-2">
                      {{ contentSuggs.suggestions.length }} suggestions generated
                    </p>

                    <div v-if="suggestionsExpanded" class="space-y-3 mt-3">
                      <div
                        v-for="(sugg, idx) in contentSuggs.suggestions"
                        :key="idx"
                        class="border border-border-light rounded p-3"
                      >
                        <p class="text-xs font-display font-medium text-primary mb-1">{{ sugg.title || sugg.page || `Suggestion ${idx + 1}` }}</p>
                        <div v-if="sugg.before" class="mb-1">
                          <p class="text-[10px] text-muted uppercase tracking-wider mb-0.5">Before</p>
                          <p class="text-xs text-secondary bg-warm-50 rounded p-1.5 line-through">{{ sugg.before }}</p>
                        </div>
                        <div v-if="sugg.after">
                          <p class="text-[10px] text-muted uppercase tracking-wider mb-0.5">After</p>
                          <div class="flex items-start justify-between gap-2">
                            <p class="text-xs text-primary bg-score-good/5 rounded p-1.5 flex-1">{{ sugg.after }}</p>
                            <button
                              @click="copyToClipboard(sugg.after)"
                              class="text-[11px] text-accent hover:text-accent-hover font-display font-medium shrink-0 mt-1"
                            >
                              {{ copiedUrl === sugg.after ? 'Copied!' : 'Copy' }}
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>
                  </template>

                  <template v-else>
                    <p class="text-xs text-secondary mb-3">
                      Get AI-powered content improvements to boost your visibility score.
                    </p>
                    <button
                      @click="handleOptimize"
                      :disabled="optimizing || !latestCompletedScan"
                      class="text-xs text-accent hover:text-accent-hover font-display font-medium disabled:opacity-50"
                    >
                      <template v-if="optimizing">
                        <svg class="w-3 h-3 animate-spin inline mr-1" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" /><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>
                        Generating...
                      </template>
                      <template v-else>Generate suggestions</template>
                    </button>
                  </template>
                </div>
              </div>
            </section>

            <!-- 5. Agent Simulator Card (full width) -->
            <section class="mb-8 animate-slide-up" style="animation-delay: 180ms">
              <div class="border border-border rounded-lg p-5 bg-surface">
                <div class="flex items-center justify-between mb-3">
                  <p class="font-display font-semibold text-sm text-primary">Agent Simulator</p>
                  <span class="text-[10px] font-display font-bold uppercase tracking-wider text-accent bg-accent/10 px-1.5 py-0.5 rounded">Pro</span>
                </div>

                <template v-if="simulation?.steps">
                  <div class="flex items-center gap-3 mb-4">
                    <p class="text-xs text-secondary">
                      Completion rate:
                      <span class="font-display font-bold tabular-nums" :class="scoreColorClass(simulationRate)">{{ simulationRate }}%</span>
                    </p>
                  </div>
                  <StepFlow :steps="simulation.steps" />
                </template>

                <template v-else>
                  <p class="text-xs text-secondary mb-3">
                    Simulate how an AI agent navigates and understands your site step by step.
                  </p>
                  <button
                    @click="handleSimulate"
                    :disabled="simulating || !latestCompletedScan"
                    class="text-xs text-accent hover:text-accent-hover font-display font-medium disabled:opacity-50"
                  >
                    <template v-if="simulating">
                      <svg class="w-3 h-3 animate-spin inline mr-1" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" /><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>
                      Running simulation...
                    </template>
                    <template v-else>Run simulation</template>
                  </button>
                </template>
              </div>
            </section>

          </template>
          <!-- END PRO WIDGETS -->

          <!-- 6. Recent Scans -->
          <section class="mb-8 animate-slide-up" :style="{ animationDelay: isPro ? '240ms' : '60ms' }">
            <div class="flex items-center justify-between mb-4">
              <h2 class="font-display text-lg font-bold tracking-tight">Recent scans</h2>
              <router-link to="/" class="text-[13px] text-accent hover:text-accent-hover transition-colors font-display font-medium">
                + New scan
              </router-link>
            </div>

            <div v-if="scans.length === 0" class="border border-dashed border-border rounded-lg p-10 text-center">
              <p class="font-display font-semibold text-primary mb-1">No scans yet</p>
              <p class="text-sm text-secondary">Run your first scan above to get started.</p>
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

          <!-- 7. UpgradeCard for free users -->
          <section v-if="!isPro" class="mb-8 animate-slide-up" style="animation-delay: 120ms">
            <UpgradeCard />
          </section>

        </template>
      </div>
    </div>
  </AppLayout>
</template>
