<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getScanResult, getScanAccess, createCheckoutSession, downloadFixFiles, runDiscoveryTest, getScanInsights } from '../api.js'
import { isLoggedIn, isPro, user, logout } from '../auth.js'
import ScoreCircle from '../components/ScoreCircle.vue'
import CategoryBar from '../components/CategoryBar.vue'
import FixCard from '../components/FixCard.vue'
import CheckItem from '../components/CheckItem.vue'

const route = useRoute()
const router = useRouter()
const scanId = route.params.id

const scan = ref(null)
const loading = ref(true)
const error = ref('')
const copied = ref(false)

// Fix file access state
const hasFixAccess = ref(false)
const checkingAccess = ref(false)
const purchasing = ref(false)
const downloading = ref(false)

// AI Insights state
const insights = ref(null)
const loadingInsights = ref(false)

// AI Discovery state
const discoveryResult = ref(null)
const discoveryLoading = ref(false)
const discoveryError = ref('')

async function loadInsights() {
  loadingInsights.value = true
  try {
    const data = await getScanInsights(scanId)
    insights.value = data.insights
  } catch (e) {
    insights.value = { error: e.message || 'Could not load insights.' }
  } finally {
    loadingInsights.value = false
  }
}

function scanCompetitors() {
  if (insights.value?.competitors) {
    const domains = [scan.value.domain, ...insights.value.competitors.slice(0, 3)]
    router.push({ name: 'Compare', query: { domains: domains.join(',') } })
  }
}

async function handleRunDiscovery() {
  discoveryLoading.value = true
  discoveryError.value = ''
  try {
    const result = await runDiscoveryTest(scanId)
    discoveryResult.value = result
  } catch (e) {
    discoveryError.value = e.message || 'Could not run discovery test.'
  } finally {
    discoveryLoading.value = false
  }
}

function handleLogout() {
  logout()
  router.push('/')
}

async function checkFixAccess() {
  if (!isLoggedIn.value) return
  checkingAccess.value = true
  try {
    const access = await getScanAccess(scanId)
    hasFixAccess.value = !!(access.has_fix_access || access.has_access)
  } catch {
    hasFixAccess.value = false
  } finally {
    checkingAccess.value = false
  }
}

async function handlePurchaseFixFiles() {
  purchasing.value = true
  try {
    const session = await createCheckoutSession('fix_files', scanId)
    const url = session.checkout_url || session.url
    if (url) {
      window.location.href = url
    }
  } catch (e) {
    error.value = e.message || 'Could not create checkout session.'
  } finally {
    purchasing.value = false
  }
}

async function handleDownloadFixes() {
  downloading.value = true
  try {
    const blob = await downloadFixFiles(scanId)
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `agentcheck-fixes-${scan.value?.domain || scanId}.zip`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  } catch (e) {
    error.value = e.message || 'Download failed.'
  } finally {
    downloading.value = false
  }
}

// Track which category sections are expanded
const expandedCategories = ref({})

function toggleCategory(key) {
  expandedCategories.value[key] = !expandedCategories.value[key]
}

const categoryDescriptions = {
  'Protocol Readiness': 'Whether AI agents can discover and connect to your shop through standard protocols like llms.txt, ai.txt, and robots.txt directives.',
  'Structured Data Quality': 'How well your product catalog is described in machine-readable formats like Schema.org, JSON-LD, and data feeds.',
  'Agent Accessibility': 'Whether agents can navigate your site, access content without JavaScript, and use clean API endpoints.',
  'Transaction Readiness': 'How prepared your shop is for programmatic purchasing — cart APIs, checkout flows, and order support.',
  'Trust Signals': 'Security and credibility indicators that agents evaluate before recommending a shop to users.',
}

const categories = computed(() => {
  if (!scan.value?.categories) return []
  return Object.entries(scan.value.categories).map(([key, val]) => ({
    key,
    name: key,
    description: categoryDescriptions[key] || '',
    score: val.score ?? 0,
    maxScore: val.max_score ?? val.max ?? 100,
    checks: (scan.value.checks || []).filter(c => c.category === key),
  }))
})

const topFixes = computed(() => {
  if (!scan.value?.fixes) return []
  return scan.value.fixes.slice(0, 5)
})

const summaryLine = computed(() => {
  if (!scan.value) return ''
  const s = scan.value.score
  if (s >= 80) return 'Your shop is well-prepared for AI agent discovery and interaction.'
  if (s >= 60) return 'Your shop has a solid foundation but several areas need attention for full AI agent readiness.'
  if (s >= 40) return 'Your shop has significant room for improvement in AI agent readiness.'
  if (s >= 20) return 'AI agents will have difficulty finding and interacting with your shop. There are critical gaps to address.'
  return 'Your shop is largely invisible to AI agents. Immediate action is needed across all areas.'
})

const scanDate = computed(() => {
  return new Date().toLocaleDateString('en-US', {
    year: 'numeric', month: 'long', day: 'numeric',
  })
})

const paymentSuccess = ref(false)

async function fetchReport() {
  try {
    const result = await getScanResult(scanId)
    if (result.status !== 'completed') {
      router.push({ name: 'ScanProgress', params: { id: scanId } })
      return
    }
    scan.value = result
    // Auto-load AI insights for Pro users
    if (isPro.value) {
      loadInsights()
    }
    // Expand categories that have failures by default
    for (const cat of categories.value) {
      if (cat.checks.some(c => c.status === 'fail')) {
        expandedCategories.value[cat.key] = true
      }
    }
    await checkFixAccess()

    // Auto-download fix files after successful payment
    if (route.query.payment === 'success' && route.query.type === 'fix_files') {
      paymentSuccess.value = true
      // Wait a moment for Stripe webhook to process, then re-check access and download
      setTimeout(async () => {
        await checkFixAccess()
        if (hasFixAccess.value) {
          handleDownloadFixes()
        }
      }, 2000)
    }
  } catch (e) {
    error.value = e.message || 'Could not load report.'
  } finally {
    loading.value = false
  }
}

function shareReport() {
  navigator.clipboard.writeText(window.location.href).then(() => {
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
  })
}

onMounted(fetchReport)
</script>

<template>
  <div class="flex-1 flex flex-col">
    <!-- Nav -->
    <nav class="border-b border-border-light">
      <div class="max-w-5xl mx-auto px-6 lg:px-8 h-14 flex items-center justify-between">
        <router-link to="/" class="flex items-center gap-2">
          <svg class="w-5 h-5 text-accent" viewBox="0 0 24 24" fill="none">
            <path d="M12 2L4 20h4l1.5-4h5L16 20h4L12 2zm0 7l2 5h-4l2-5z" fill="currentColor"/>
            <path d="M20 8a10 10 0 00-4-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" opacity="0.5"/>
            <path d="M22 6a14 14 0 00-6-5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" opacity="0.3"/>
          </svg>
          <span class="font-display font-bold text-[15px] tracking-tight">AgentCheck</span>
        </router-link>
        <div class="flex items-center gap-1">
          <router-link v-if="isLoggedIn" to="/dashboard" class="btn-ghost">
            <svg class="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
            </svg>
            Back to dashboard
          </router-link>
          <router-link v-else to="/" class="btn-ghost">
            <svg class="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
            </svg>
            Back to home
          </router-link>
          <router-link to="/pricing" class="btn-ghost">Pricing</router-link>
          <button @click="shareReport" class="btn-ghost">
            <svg class="w-4 h-4 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
            </svg>
            {{ copied ? 'Link copied!' : 'Share report' }}
          </button>
          <router-link :to="{ name: 'Badge', params: { id: scanId } }" class="btn-ghost">
            Download badge
          </router-link>
          <router-link v-if="isLoggedIn" to="/dashboard" class="btn-ghost">Dashboard</router-link>
          <template v-if="isLoggedIn">
            <div
              class="w-7 h-7 rounded-full bg-accent text-white flex items-center justify-center text-xs font-display font-bold ml-1"
              :title="user?.email"
            >
              {{ user?.email?.[0]?.toUpperCase() || '?' }}
            </div>
          </template>
          <router-link v-else :to="{ name: 'Login', query: { redirect: $route.fullPath } }" class="btn-ghost">Sign in</router-link>
        </div>
      </div>
    </nav>

    <!-- Loading -->
    <div v-if="loading" class="flex-1 flex items-center justify-center">
      <div class="text-center">
        <svg class="w-6 h-6 text-accent animate-spin mx-auto mb-3" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
        <p class="text-sm text-secondary">Loading report...</p>
      </div>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="flex-1 flex items-center justify-center px-6">
      <div>
        <h2 class="font-display text-xl font-bold mb-2 text-score-bad">Could not load report</h2>
        <p class="text-secondary mb-6 text-sm">{{ error }}</p>
        <router-link to="/" class="btn-primary">Back to home</router-link>
      </div>
    </div>

    <!-- Report -->
    <div v-else-if="scan" class="flex-1">

      <!-- ─── Header ─── -->
      <div class="border-b border-border-light bg-warm-50">
        <div class="max-w-4xl mx-auto px-6 lg:px-8 py-10 animate-fade-in">
          <div class="flex flex-col sm:flex-row sm:items-center gap-6 sm:gap-10">
            <!-- Score circle — compact, not hero-sized -->
            <ScoreCircle :score="scan.score" :grade="scan.grade" :size="96" class="flex-shrink-0" />
            <!-- Domain + summary -->
            <div class="min-w-0">
              <p class="section-label mb-1">Report for</p>
              <h1 class="font-display text-2xl font-bold tracking-tight text-primary mb-2 truncate">{{ scan.domain }}</h1>
              <p class="text-sm text-secondary leading-relaxed prose-body">{{ summaryLine }}</p>
              <p class="text-xs text-muted mt-2">Scanned {{ scanDate }}</p>
            </div>
          </div>
        </div>
      </div>

      <div class="max-w-4xl mx-auto px-6 lg:px-8 py-10">

        <!-- ─── AI Insights (Pro) ─── -->
        <section v-if="isLoggedIn" class="mb-14 animate-slide-up">
          <div class="flex items-center gap-2 mb-4">
            <h2 class="font-display text-lg font-bold tracking-tight">AI Insights</h2>
            <span class="text-[10px] font-display font-bold text-white bg-accent px-1.5 py-0.5 rounded uppercase tracking-wider">Pro</span>
          </div>

          <div v-if="!isPro" class="border border-accent/20 rounded-lg p-5 bg-accent/[0.03]">
            <p class="text-sm text-secondary mb-3">Get AI-powered competitor analysis, smart recommendations, and visibility assessment.</p>
            <router-link to="/pricing" class="btn-primary text-sm">Upgrade to Pro</router-link>
          </div>

          <div v-else>
            <button v-if="!insights && !loadingInsights" @click="loadInsights" class="btn-secondary text-sm">
              Generate AI insights
            </button>

            <div v-if="loadingInsights" class="flex items-center gap-2 text-sm text-secondary">
              <svg class="w-4 h-4 animate-spin text-accent" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Analyzing with AI...
            </div>

            <div v-if="insights && !insights.error" class="space-y-6">
              <!-- Visibility Summary -->
              <div class="border-l-2 border-accent pl-4">
                <p class="text-sm text-primary leading-relaxed">{{ insights.visibility_summary }}</p>
                <p v-if="insights.estimated_improvement" class="text-xs text-accent mt-1 font-display font-medium">
                  Estimated improvement: {{ insights.estimated_improvement }}
                </p>
              </div>

              <!-- Priority Actions -->
              <div v-if="insights.priority_actions?.length">
                <p class="section-label mb-2">Priority actions</p>
                <ol class="space-y-2">
                  <li v-for="(action, idx) in insights.priority_actions" :key="idx" class="flex gap-3 text-sm">
                    <span class="flex-shrink-0 w-5 h-5 rounded-full bg-accent text-white text-xs font-display font-bold flex items-center justify-center">{{ idx + 1 }}</span>
                    <span class="text-secondary leading-relaxed">{{ action }}</span>
                  </li>
                </ol>
              </div>

              <!-- Competitors -->
              <div v-if="insights.competitors?.length">
                <div class="flex items-center justify-between mb-2">
                  <p class="section-label">Detected competitors</p>
                  <button @click="scanCompetitors" class="text-xs text-accent hover:text-accent-hover font-display font-medium">
                    Compare all →
                  </button>
                </div>
                <div class="flex flex-wrap gap-2">
                  <span v-for="comp in insights.competitors" :key="comp"
                    class="inline-flex items-center text-xs font-display bg-warm-100 text-secondary px-2.5 py-1 rounded-md">
                    {{ comp }}
                  </span>
                </div>
                <p v-if="insights.market_segment" class="text-xs text-muted mt-2">
                  Market: {{ insights.market_segment }}
                </p>
              </div>
            </div>

            <div v-if="insights?.error" class="text-sm text-score-bad">
              {{ insights.error }}
            </div>
          </div>
        </section>

        <!-- ─── Top Fixes ─── -->
        <section v-if="topFixes.length > 0" class="mb-14 animate-slide-up">
          <h2 class="font-display text-lg font-bold tracking-tight mb-1">Priority fixes</h2>
          <p class="text-sm text-secondary mb-5">The highest-impact changes you can make, ordered by importance.</p>
          <div class="space-y-3">
            <FixCard v-for="(fix, idx) in topFixes" :key="idx" :fix="fix" />
          </div>
        </section>

        <!-- ─── Category Breakdown ─── -->
        <section class="mb-14 animate-slide-up" style="animation-delay: 100ms">
          <h2 class="font-display text-lg font-bold tracking-tight mb-1">Category breakdown</h2>
          <p class="text-sm text-secondary mb-6">Each category measures a different dimension of AI agent compatibility.</p>

          <div class="space-y-6">
            <div v-for="cat in categories" :key="cat.key">
              <!-- Category header with bar -->
              <button
                @click="toggleCategory(cat.key)"
                class="w-full text-left focus-visible:outline-none group"
              >
                <CategoryBar :name="cat.name" :score="cat.score" :max-score="cat.maxScore" />
                <div class="flex items-center gap-2 mt-1.5">
                  <p class="text-xs text-muted leading-relaxed flex-1">{{ cat.description }}</p>
                  <svg
                    class="w-3.5 h-3.5 text-warm-400 flex-shrink-0 transition-transform duration-200"
                    :class="{ 'rotate-180': expandedCategories[cat.key] }"
                    fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"
                  >
                    <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
                  </svg>
                </div>
              </button>

              <!-- Expanded checks list -->
              <Transition
                enter-active-class="transition-all duration-250 ease-out"
                enter-from-class="max-h-0 opacity-0"
                enter-to-class="max-h-[1200px] opacity-100"
                leave-active-class="transition-all duration-200 ease-in"
                leave-from-class="max-h-[1200px] opacity-100"
                leave-to-class="max-h-0 opacity-0"
              >
                <div v-if="expandedCategories[cat.key]" class="overflow-hidden mt-3 ml-0 pl-4 border-l border-border-light">
                  <div v-if="cat.checks.length === 0" class="py-3 text-sm text-muted">
                    No individual checks available for this category.
                  </div>
                  <CheckItem
                    v-for="(check, idx) in cat.checks"
                    :key="idx"
                    :name="check.name"
                    :status="check.status"
                    :message="check.message"
                  />
                </div>
              </Transition>
            </div>
          </div>
        </section>

        <!-- ─── AI Discovery Test ─── -->
        <section class="mb-14 animate-slide-up" style="animation-delay: 120ms">
          <div class="flex items-center gap-3 mb-1">
            <h2 class="font-display text-lg font-bold tracking-tight">AI Discovery Test</h2>
            <span class="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-display font-bold uppercase tracking-wider bg-accent/10 text-accent">Beta</span>
          </div>
          <p class="text-sm text-secondary mb-5">We query real AI assistants to check if they know about your store.</p>

          <!-- Pro user: can run the test -->
          <template v-if="isPro">
            <!-- Not run yet -->
            <div v-if="!discoveryResult && !discoveryLoading && !discoveryError" class="border border-border rounded-lg p-6 bg-surface">
              <p class="text-sm text-secondary mb-4">Run a discovery test to see if AI agents like ChatGPT, Claude, and Perplexity mention your store when asked shopping-related questions.</p>
              <button @click="handleRunDiscovery" class="btn-primary">
                Run discovery test
              </button>
            </div>

            <!-- Loading -->
            <div v-if="discoveryLoading" class="border border-border rounded-lg p-6 bg-surface text-center">
              <svg class="w-5 h-5 text-accent animate-spin mx-auto mb-3" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              <p class="text-sm text-secondary">Querying AI providers... This may take a minute.</p>
            </div>

            <!-- Error -->
            <div v-if="discoveryError" class="border border-score-bad/20 rounded-lg p-5 bg-score-bad/[0.03]">
              <p class="text-sm text-score-bad mb-3">{{ discoveryError }}</p>
              <button @click="handleRunDiscovery" class="btn-secondary text-sm">Try again</button>
            </div>

            <!-- Results -->
            <div v-if="discoveryResult" class="border border-border rounded-lg overflow-hidden">
              <!-- Score header -->
              <div class="px-6 py-5 bg-surface border-b border-border-light flex items-center gap-6">
                <div class="flex-shrink-0">
                  <div
                    class="w-16 h-16 rounded-full border-[3px] flex items-center justify-center"
                    :class="{
                      'border-score-good': discoveryResult.discovery_score >= 60,
                      'border-score-medium': discoveryResult.discovery_score >= 30 && discoveryResult.discovery_score < 60,
                      'border-score-bad': discoveryResult.discovery_score < 30,
                    }"
                  >
                    <span
                      class="font-display font-bold text-xl"
                      :class="{
                        'text-score-good': discoveryResult.discovery_score >= 60,
                        'text-score-medium': discoveryResult.discovery_score >= 30 && discoveryResult.discovery_score < 60,
                        'text-score-bad': discoveryResult.discovery_score < 30,
                      }"
                    >{{ discoveryResult.discovery_score }}%</span>
                  </div>
                </div>
                <div>
                  <p class="font-display font-semibold text-primary">Discovery Score</p>
                  <p class="text-sm text-secondary mt-0.5">Found in {{ discoveryResult.queries_found }} of {{ discoveryResult.queries_tested }} AI queries</p>
                </div>
              </div>
              <!-- Summary -->
              <div class="px-6 py-4 bg-warm-50 border-b border-border-light">
                <p class="text-sm text-secondary leading-relaxed">{{ discoveryResult.summary }}</p>
              </div>
              <!-- Individual results -->
              <div class="divide-y divide-border-light">
                <div v-for="(r, idx) in discoveryResult.results" :key="idx" class="px-6 py-4">
                  <div class="flex items-start gap-3">
                    <div class="flex-shrink-0 mt-0.5">
                      <span v-if="r.found" class="inline-flex w-5 h-5 rounded-full bg-score-good/10 items-center justify-center">
                        <svg class="w-3 h-3 text-score-good" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
                          <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
                        </svg>
                      </span>
                      <span v-else class="inline-flex w-5 h-5 rounded-full bg-score-bad/10 items-center justify-center">
                        <svg class="w-3 h-3 text-score-bad" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
                          <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </span>
                    </div>
                    <div class="min-w-0 flex-1">
                      <p class="text-sm font-display font-medium text-primary">"{{ r.query }}"</p>
                      <div class="flex items-center gap-2 mt-1">
                        <span class="text-[11px] font-display uppercase tracking-wider px-1.5 py-0.5 rounded bg-warm-100 text-muted">{{ r.provider }}</span>
                        <span class="text-xs" :class="r.found ? 'text-score-good' : 'text-score-bad'">{{ r.found ? 'Found' : 'Not found' }}</span>
                      </div>
                      <p class="text-xs text-muted mt-1.5 leading-relaxed">{{ r.context }}</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </template>

          <!-- Non-Pro user: teaser -->
          <template v-else>
            <div class="border border-accent/20 rounded-lg p-6 bg-accent/[0.03]">
              <p class="text-sm text-secondary mb-2">
                With the AI Discovery Test, we query ChatGPT, Claude, and Perplexity with real shopping queries and check if your store actually appears in the responses. See exactly where you are found and where you are not.
              </p>
              <p class="text-xs text-muted mb-4">Available on the Pro plan.</p>
              <router-link to="/pricing" class="btn-primary text-sm">Upgrade to Pro</router-link>
            </div>
          </template>
        </section>

        <!-- ─── Payment success banner ─── -->
        <div v-if="paymentSuccess" class="mb-6 border border-score-good/30 rounded-lg p-4 bg-score-good/5 flex items-center gap-3 animate-fade-in">
          <svg class="w-5 h-5 text-score-good flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p class="text-sm text-score-good font-display font-medium">Payment successful! Your fix files are downloading...</p>
        </div>

        <!-- ─── Fix Files CTA ─── -->
        <section class="mb-14 border border-accent/20 rounded-lg p-6 bg-accent/[0.03] animate-slide-up" style="animation-delay: 150ms">
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h3 class="font-display font-semibold text-primary">Get tailored fix files for {{ scan.domain }}</h3>
              <p class="text-sm text-secondary mt-1 leading-relaxed">Download ready-to-deploy ai.txt, llms.txt, Schema markup, and more — customized for your scan results.</p>
            </div>
            <div class="flex flex-col items-end gap-1 flex-shrink-0">
              <!-- Has access: download button -->
              <template v-if="isLoggedIn && hasFixAccess">
                <button
                  @click="handleDownloadFixes"
                  class="btn-primary"
                  :disabled="downloading"
                >
                  <svg v-if="downloading" class="w-4 h-4 mr-2 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  {{ downloading ? 'Downloading...' : 'Download fix files' }}
                </button>
                <span class="text-xs text-score-good">Access granted</span>
              </template>
              <!-- Logged in, no access: purchase -->
              <template v-else-if="isLoggedIn && !hasFixAccess">
                <button
                  @click="handlePurchaseFixFiles"
                  class="btn-primary"
                  :disabled="purchasing"
                >
                  <svg v-if="purchasing" class="w-4 h-4 mr-2 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  {{ purchasing ? 'Redirecting...' : 'Get fix files — $9' }}
                </button>
                <span class="text-xs text-muted">or included in Pro</span>
              </template>
              <!-- Not logged in -->
              <template v-else>
                <router-link
                  :to="{ name: 'Login', query: { redirect: $route.fullPath } }"
                  class="btn-primary"
                >
                  Sign in to get fix files
                </router-link>
                <span class="text-xs text-muted">$9 one-time or included in Pro</span>
              </template>
            </div>
          </div>
        </section>

        <!-- ─── Actions row ─── -->
        <section class="border-t border-border-light pt-8 mb-10 animate-slide-up" style="animation-delay: 200ms">
          <div class="flex flex-wrap gap-3">
            <button @click="shareReport" class="btn-secondary">
              {{ copied ? 'Link copied!' : 'Share report' }}
            </button>
            <router-link :to="{ name: 'Badge', params: { id: scanId } }" class="btn-secondary">
              Download badge
            </router-link>
            <router-link to="/" class="btn-secondary">
              Run new scan
            </router-link>
          </div>
        </section>
      </div>

      <!-- Footer -->
      <footer class="border-t border-border-light py-6 px-6 lg:px-8">
        <div class="max-w-4xl mx-auto flex items-center justify-between">
          <span class="text-xs text-muted">&copy; {{ new Date().getFullYear() }} AgentCheck</span>
          <div class="flex items-center gap-5 text-xs text-muted">
            <router-link to="/privacy" class="hover:text-secondary transition-colors">Privacy Policy</router-link>
            <router-link to="/terms" class="hover:text-secondary transition-colors">Terms of Service</router-link>
            <router-link to="/imprint" class="hover:text-secondary transition-colors">Imprint</router-link>
            <a
              href="https://github.com/lennystepn-hue/agentready"
              target="_blank"
              rel="noopener"
              class="hover:text-secondary transition-colors"
            >
              GitHub
            </a>
          </div>
        </div>
      </footer>
    </div>
  </div>
</template>
