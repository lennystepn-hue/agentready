<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getScanResult, getScanAccess, createCheckoutSession, downloadFixFiles, runDiscoveryTest, getScanInsights } from '../api.js'
import { isLoggedIn, isPro, user, logout } from '../auth.js'
import AppHeader from '../components/AppHeader.vue'
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
  // Pro users always have access
  if (isPro.value) {
    hasFixAccess.value = true
    return
  }
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
  'Protocol Readiness': 'Whether AI agents can discover and connect to your site through standard protocols like llms.txt, ai.txt, and robots.txt directives.',
  'Structured Data Quality': 'How well your content is described in machine-readable formats like Schema.org, JSON-LD, and data feeds.',
  'Agent Accessibility': 'Whether agents can navigate your site, access content without JavaScript, and use clean API endpoints.',
  'Conversion Readiness': 'How prepared your site is for AI-driven conversions — CTAs, contact forms, booking, and conversion paths.',
  'Trust Signals': 'Security and credibility indicators that agents evaluate before recommending your site to users.',
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

const criticalFixes = computed(() => {
  if (!scan.value?.fixes) return []
  return scan.value.fixes.slice(0, 3)
})

const summaryLine = computed(() => {
  if (!scan.value) return ''
  const s = scan.value.score
  if (s >= 80) return 'Your site is well-prepared for AI agent discovery and interaction.'
  if (s >= 60) return 'Your site has a solid foundation but several areas need attention for full AI agent readiness.'
  if (s >= 40) return 'Your site has significant room for improvement in AI agent readiness.'
  if (s >= 20) return 'AI agents will have difficulty finding and interacting with your site. There are critical gaps to address.'
  return 'Your site is largely invisible to AI agents. Immediate action is needed across all areas.'
})

const scanDate = computed(() => {
  return new Date().toLocaleDateString('en-US', {
    year: 'numeric', month: 'long', day: 'numeric',
  })
})

// Visibility tier badge
const visibilityTier = computed(() => {
  if (!scan.value) return null
  const s = scan.value.score
  if (s >= 80) return { label: 'Highly Visible', color: 'text-score-good', bg: 'bg-score-good/10', border: 'border-score-good/30' }
  if (s >= 60) return { label: 'Partially Visible', color: 'text-score-medium', bg: 'bg-score-medium/10', border: 'border-score-medium/30' }
  if (s >= 35) return { label: 'Mostly Hidden', color: 'text-score-bad', bg: 'bg-score-bad/10', border: 'border-score-bad/30' }
  return { label: 'Invisible to AI', color: 'text-score-bad', bg: 'bg-score-bad/10', border: 'border-score-bad/30' }
})

// "Get Found" strip — maps AI assistants to category signals
const getFoundStatus = computed(() => {
  if (!scan.value) return []
  const cats = scan.value.categories || {}

  // Helper: get score percentage for a category key
  const pct = (key) => {
    const cat = cats[key]
    if (!cat) return 0
    const max = cat.max_score ?? cat.max ?? 100
    return max > 0 ? Math.round(((cat.score ?? 0) / max) * 100) : 0
  }

  const protocolPct = pct('Protocol Readiness')
  const structuredPct = pct('Structured Data Quality')
  const accessPct = pct('Agent Accessibility')
  const trustPct = pct('Trust Signals')

  // Each AI assistant has different weighting heuristics
  return [
    {
      name: 'ChatGPT',
      found: protocolPct >= 50 && structuredPct >= 40,
      reason: protocolPct < 50 ? 'Missing llms.txt or ai.txt' : structuredPct < 40 ? 'Weak structured data' : 'Protocol & schema ready',
    },
    {
      name: 'Claude',
      found: protocolPct >= 60 && accessPct >= 50,
      reason: protocolPct < 60 ? 'Protocol readiness too low' : accessPct < 50 ? 'Agent accessibility issues' : 'Content accessible',
    },
    {
      name: 'Perplexity',
      found: structuredPct >= 50 && trustPct >= 50,
      reason: structuredPct < 50 ? 'Insufficient structured data' : trustPct < 50 ? 'Low trust signals' : 'Indexable & trusted',
    },
    {
      name: 'Gemini',
      found: structuredPct >= 45 && protocolPct >= 40,
      reason: structuredPct < 45 ? 'Schema markup needed' : protocolPct < 40 ? 'Crawl directives missing' : 'Schema & crawl ready',
    },
  ]
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
    <AppHeader :show-back="isLoggedIn ? '/dashboard' : '/'" :back-label="isLoggedIn ? 'Dashboard' : 'Home'">
      <template #actions>
        <button
          @click="shareReport"
          class="text-[13px] text-secondary hover:text-primary transition-colors flex items-center gap-1.5 font-display font-medium"
        >
          <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
          </svg>
          {{ copied ? 'Copied!' : 'Share' }}
        </button>
      </template>
    </AppHeader>

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
    <div v-else-if="scan" class="flex-1 pb-24 sm:pb-10">

      <!-- ─── HERO HEADER ─── -->
      <div class="border-b border-border bg-warm-50 relative overflow-hidden">
        <!-- Subtle texture strip -->
        <div class="absolute inset-0 pointer-events-none"
          style="background: repeating-linear-gradient(-55deg, transparent, transparent 60px, rgba(13,115,119,0.018) 60px, rgba(13,115,119,0.018) 61px);"
        />
        <div class="max-w-4xl mx-auto px-6 lg:px-8 py-8 animate-fade-in relative z-10">
          <!-- Top meta row -->
          <div class="flex items-center gap-2 mb-5">
            <p class="section-label">AI Visibility Report</p>
            <span class="text-warm-300">·</span>
            <p class="text-xs text-muted font-body">{{ scanDate }}</p>
          </div>

          <!-- Score + Domain row -->
          <div class="flex flex-col sm:flex-row sm:items-center gap-6 sm:gap-8">
            <ScoreCircle :score="scan.score" :grade="scan.grade" :size="100" class="flex-shrink-0" />

            <div class="flex-1 min-w-0">
              <div class="flex flex-wrap items-center gap-2 mb-1.5">
                <h1 class="font-display text-2xl font-bold tracking-tight text-primary">{{ scan.domain }}</h1>
                <span v-if="scan.site_label"
                  class="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-display font-bold uppercase tracking-wider bg-warm-200 text-warm-600">
                  {{ scan.site_label }}
                </span>
              </div>
              <!-- Visibility tier badge -->
              <div v-if="visibilityTier" class="mb-2.5">
                <span
                  class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-display font-semibold border"
                  :class="[visibilityTier.color, visibilityTier.bg, visibilityTier.border]"
                >
                  <span class="w-1.5 h-1.5 rounded-full"
                    :class="{
                      'bg-score-good': scan.score >= 80,
                      'bg-score-medium': scan.score >= 60 && scan.score < 80,
                      'bg-score-bad': scan.score < 60,
                    }"
                  />
                  {{ visibilityTier.label }}
                </span>
              </div>
              <p class="text-sm text-secondary leading-relaxed max-w-prose">{{ summaryLine }}</p>
            </div>

            <!-- Action cluster (desktop) -->
            <div class="hidden sm:flex flex-col items-end gap-2 flex-shrink-0">
              <template v-if="isLoggedIn && hasFixAccess">
                <button @click="handleDownloadFixes" :disabled="downloading" class="btn-primary whitespace-nowrap">
                  <svg v-if="downloading" class="w-4 h-4 mr-1.5 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  <svg v-else class="w-4 h-4 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                  </svg>
                  {{ downloading ? 'Downloading...' : 'Download Fix Files' }}
                </button>
                <span class="text-[11px] text-score-good font-display font-medium">Included in your plan</span>
              </template>
              <template v-else-if="isLoggedIn">
                <button @click="handlePurchaseFixFiles" :disabled="purchasing" class="btn-primary whitespace-nowrap">
                  <svg v-if="purchasing" class="w-4 h-4 mr-1.5 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  <svg v-else class="w-4 h-4 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                  </svg>
                  {{ purchasing ? 'Redirecting...' : 'Get Fix Files — $9' }}
                </button>
                <span class="text-[11px] text-muted">or included in Pro</span>
              </template>
              <template v-else>
                <router-link :to="{ name: 'Login', query: { redirect: $route.fullPath } }" class="btn-primary whitespace-nowrap">
                  Get Fix Files
                </router-link>
                <span class="text-[11px] text-muted">$9 one-time · or included in Pro</span>
              </template>
            </div>
          </div>
        </div>
      </div>

      <!-- ─── GET FOUND STRIP ─── -->
      <div class="border-b border-border-light bg-surface animate-fade-in" style="animation-delay: 80ms">
        <div class="max-w-4xl mx-auto px-6 lg:px-8 py-4">
          <div class="flex items-center gap-2 mb-3">
            <p class="section-label">Can AI find you?</p>
            <span class="text-[11px] text-muted font-body">Based on your scan results</span>
          </div>
          <div class="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
            <div
              v-for="ai in getFoundStatus"
              :key="ai.name"
              class="flex items-center gap-2.5 px-3 py-2.5 rounded-lg border transition-colors duration-150"
              :class="ai.found
                ? 'bg-score-good/[0.04] border-score-good/20'
                : 'bg-score-bad/[0.04] border-score-bad/15'"
            >
              <!-- Status dot -->
              <div class="flex-shrink-0">
                <div v-if="ai.found" class="w-5 h-5 rounded-full bg-score-good/15 flex items-center justify-center">
                  <svg class="w-3 h-3 text-score-good" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <div v-else class="w-5 h-5 rounded-full bg-score-bad/15 flex items-center justify-center">
                  <svg class="w-3 h-3 text-score-bad" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </div>
              </div>
              <div class="min-w-0">
                <p class="text-xs font-display font-semibold text-primary leading-tight">{{ ai.name }}</p>
                <p class="text-[10px] leading-tight mt-0.5 truncate"
                  :class="ai.found ? 'text-score-good' : 'text-score-bad'">
                  {{ ai.found ? 'Can find you' : 'Cannot find you' }}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ─── MAIN CONTENT ─── -->
      <div class="max-w-4xl mx-auto px-6 lg:px-8 py-10 space-y-14">

        <!-- ─── Payment success banner ─── -->
        <div v-if="paymentSuccess" class="border border-score-good/30 rounded-lg p-4 bg-score-good/5 flex items-center gap-3 animate-fade-in">
          <svg class="w-5 h-5 text-score-good flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p class="text-sm text-score-good font-display font-medium">Payment successful! Your fix files are downloading...</p>
        </div>

        <!-- ─── DO THESE FIRST (Top 3 Fixes) ─── -->
        <section v-if="criticalFixes.length > 0" class="animate-slide-up">
          <!-- Section header -->
          <div class="flex items-start justify-between gap-4 mb-5">
            <div>
              <div class="flex items-center gap-2.5 mb-1">
                <span class="inline-flex items-center justify-center w-5 h-5 rounded-full bg-score-bad text-white text-[10px] font-display font-bold">!</span>
                <h2 class="font-display text-lg font-bold tracking-tight text-primary">Do These First</h2>
              </div>
              <p class="text-sm text-secondary">Highest-impact changes to improve your AI visibility score.</p>
            </div>
            <span class="flex-shrink-0 inline-flex items-center px-2 py-0.5 rounded text-[10px] font-display font-bold uppercase tracking-wider bg-score-bad/10 text-score-bad border border-score-bad/20 mt-0.5">
              {{ criticalFixes.filter(f => f.status === 'fail').length }} Critical
            </span>
          </div>

          <div class="space-y-2.5">
            <div
              v-for="(fix, idx) in criticalFixes"
              :key="idx"
              class="relative"
            >
              <!-- Priority number marker -->
              <div class="absolute -left-0.5 top-4 w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-display font-bold z-10 flex-shrink-0"
                :class="idx === 0 ? 'bg-score-bad text-white' : 'bg-warm-200 text-warm-600'"
              >
                {{ idx + 1 }}
              </div>
              <div class="pl-6">
                <FixCard :fix="fix" />
              </div>
            </div>
          </div>

          <!-- Download Fix Files CTA -->
          <div class="mt-6 rounded-xl border border-accent/25 bg-accent/[0.04] p-5">
            <div class="flex flex-col sm:flex-row sm:items-center gap-4">
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 mb-1">
                  <svg class="w-4 h-4 text-accent flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                  </svg>
                  <h3 class="font-display font-semibold text-primary text-sm">Ready-to-deploy fix files for {{ scan.domain }}</h3>
                </div>
                <p class="text-sm text-secondary leading-relaxed">Get customized ai.txt, llms.txt, Schema markup, and structured data files — tailored to your scan results.</p>
              </div>
              <div class="flex flex-col items-start sm:items-end gap-1 flex-shrink-0">
                <template v-if="isLoggedIn && hasFixAccess">
                  <button @click="handleDownloadFixes" :disabled="downloading" class="btn-primary">
                    <svg v-if="downloading" class="w-4 h-4 mr-1.5 animate-spin" fill="none" viewBox="0 0 24 24">
                      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    {{ downloading ? 'Downloading...' : 'Download Fix Files' }}
                  </button>
                  <span class="text-xs text-score-good font-display font-medium">Access granted</span>
                </template>
                <template v-else-if="isLoggedIn">
                  <button @click="handlePurchaseFixFiles" :disabled="purchasing" class="btn-primary">
                    <svg v-if="purchasing" class="w-4 h-4 mr-1.5 animate-spin" fill="none" viewBox="0 0 24 24">
                      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    {{ purchasing ? 'Redirecting...' : 'Get Fix Files — $9' }}
                  </button>
                  <span class="text-xs text-muted">or included in Pro</span>
                </template>
                <template v-else>
                  <router-link :to="{ name: 'Login', query: { redirect: $route.fullPath } }" class="btn-primary">
                    Sign in to get fix files
                  </router-link>
                  <span class="text-xs text-muted">$9 one-time · or included in Pro</span>
                </template>
              </div>
            </div>
          </div>
        </section>

        <!-- ─── AI INSIGHTS (Pro) ─── -->
        <section v-if="isLoggedIn" class="animate-slide-up" style="animation-delay: 60ms">
          <div class="flex items-center gap-2.5 mb-4">
            <h2 class="font-display text-lg font-bold tracking-tight">AI Insights</h2>
            <span class="text-[10px] font-display font-bold text-white bg-accent px-1.5 py-0.5 rounded uppercase tracking-wider">Pro</span>
          </div>

          <!-- Not Pro: upgrade prompt -->
          <div v-if="!isPro" class="border border-accent/20 rounded-lg p-5 bg-accent/[0.03] flex flex-col sm:flex-row sm:items-center gap-4">
            <div class="flex-1">
              <p class="text-sm font-display font-medium text-primary mb-1">Unlock AI-powered competitor analysis</p>
              <p class="text-sm text-secondary">Get smart recommendations, visibility assessment, and estimated score improvement.</p>
            </div>
            <router-link to="/pricing" class="btn-primary flex-shrink-0">Upgrade to Pro</router-link>
          </div>

          <!-- Pro: insights content -->
          <div v-else class="border border-border rounded-xl overflow-hidden bg-surface">
            <!-- Load trigger -->
            <div v-if="!insights && !loadingInsights" class="px-5 py-5 flex items-center justify-between">
              <p class="text-sm text-secondary">Competitor analysis, smart recommendations, and score improvement estimate.</p>
              <button @click="loadInsights" class="btn-secondary text-sm flex-shrink-0 ml-4">
                Generate Insights
              </button>
            </div>

            <!-- Loading -->
            <div v-if="loadingInsights" class="px-5 py-5 flex items-center gap-3 text-sm text-secondary">
              <svg class="w-4 h-4 animate-spin text-accent flex-shrink-0" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Analyzing with AI...
            </div>

            <!-- Insights loaded -->
            <div v-if="insights && !insights.error">
              <!-- Key stat bar -->
              <div v-if="insights.estimated_improvement" class="px-5 py-3.5 bg-accent/[0.05] border-b border-accent/15 flex items-center gap-3">
                <svg class="w-4 h-4 text-accent flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                </svg>
                <p class="text-sm font-display font-medium text-accent">Estimated improvement: <span class="font-bold">{{ insights.estimated_improvement }}</span></p>
              </div>

              <div class="px-5 py-4 space-y-5">
                <!-- Visibility Summary -->
                <div v-if="insights.visibility_summary">
                  <p class="section-label mb-2">Visibility summary</p>
                  <p class="text-sm text-primary leading-relaxed border-l-2 border-accent/30 pl-3">{{ insights.visibility_summary }}</p>
                </div>

                <!-- Priority Actions -->
                <div v-if="insights.priority_actions?.length">
                  <p class="section-label mb-2.5">Priority actions</p>
                  <ol class="space-y-2.5">
                    <li v-for="(action, idx) in insights.priority_actions" :key="idx" class="flex gap-3 text-sm">
                      <span class="flex-shrink-0 w-5 h-5 rounded-full bg-accent text-white text-[10px] font-display font-bold flex items-center justify-center mt-0.5">{{ idx + 1 }}</span>
                      <span class="text-secondary leading-relaxed">{{ action }}</span>
                    </li>
                  </ol>
                </div>

                <!-- Competitors -->
                <div v-if="insights.competitors?.length">
                  <div class="flex items-center justify-between mb-2">
                    <p class="section-label">Detected competitors</p>
                    <button @click="scanCompetitors" class="text-xs text-accent hover:text-accent-hover font-display font-medium min-h-[44px] flex items-center transition-colors">
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
            </div>

            <!-- Error -->
            <div v-if="insights?.error" class="px-5 py-4 text-sm text-score-bad">{{ insights.error }}</div>
          </div>
        </section>

        <!-- ─── CATEGORY BREAKDOWN ─── -->
        <section class="animate-slide-up" style="animation-delay: 100ms">
          <div class="mb-5">
            <h2 class="font-display text-lg font-bold tracking-tight mb-1">Category Breakdown</h2>
            <p class="text-sm text-secondary">Each dimension measures a different aspect of AI agent compatibility.</p>
          </div>

          <div class="space-y-5">
            <div
              v-for="cat in categories"
              :key="cat.key"
              class="border border-border-light rounded-xl overflow-hidden transition-all duration-150"
              :class="expandedCategories[cat.key] ? 'bg-surface' : 'bg-warm-50 hover:bg-surface'"
            >
              <!-- Category header (clickable) -->
              <button
                @click="toggleCategory(cat.key)"
                class="w-full text-left px-5 py-4 focus-visible:outline-none group"
              >
                <CategoryBar :name="cat.name" :score="cat.score" :max-score="cat.maxScore" />
                <div class="flex items-center justify-between mt-2">
                  <p class="text-xs text-muted leading-relaxed flex-1 pr-4 text-left">{{ cat.description }}</p>
                  <div class="flex items-center gap-1.5 flex-shrink-0">
                    <span v-if="cat.checks.filter(c => c.status === 'fail').length > 0"
                      class="text-[10px] font-display font-semibold text-score-bad bg-score-bad/10 px-1.5 py-0.5 rounded">
                      {{ cat.checks.filter(c => c.status === 'fail').length }} failing
                    </span>
                    <svg
                      class="w-3.5 h-3.5 text-warm-400 transition-transform duration-200"
                      :class="{ 'rotate-180': expandedCategories[cat.key] }"
                      fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"
                    >
                      <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
                    </svg>
                  </div>
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
                <div v-if="expandedCategories[cat.key]" class="overflow-hidden border-t border-border-light">
                  <div class="px-5 pb-2">
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
                </div>
              </Transition>
            </div>
          </div>
        </section>

        <!-- ─── AI DISCOVERY TEST ─── -->
        <section class="animate-slide-up" style="animation-delay: 120ms">
          <div class="flex items-center gap-3 mb-1">
            <h2 class="font-display text-lg font-bold tracking-tight">AI Discovery Test</h2>
            <span class="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-display font-bold uppercase tracking-wider bg-accent/10 text-accent border border-accent/20">Beta</span>
          </div>
          <p class="text-sm text-secondary mb-5">We query real AI assistants to check if they know about your site.</p>

          <!-- Pro user: can run the test -->
          <template v-if="isPro">
            <!-- Not run yet -->
            <div v-if="!discoveryResult && !discoveryLoading && !discoveryError" class="border border-border rounded-xl p-6 bg-surface">
              <p class="text-sm text-secondary mb-4 max-w-prose">Run a discovery test to see if AI agents like ChatGPT, Claude, and Perplexity mention your site when asked relevant questions.</p>
              <button @click="handleRunDiscovery" class="btn-primary">
                <svg class="w-4 h-4 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                Run AI Discovery Test
              </button>
            </div>

            <!-- Loading -->
            <div v-if="discoveryLoading" class="border border-border rounded-xl p-6 bg-surface text-center">
              <svg class="w-5 h-5 text-accent animate-spin mx-auto mb-3" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              <p class="text-sm text-secondary">Querying AI providers... This may take a minute.</p>
            </div>

            <!-- Error -->
            <div v-if="discoveryError" class="border border-score-bad/20 rounded-xl p-5 bg-score-bad/[0.03]">
              <p class="text-sm text-score-bad mb-3">{{ discoveryError }}</p>
              <button @click="handleRunDiscovery" class="btn-secondary text-sm">Try again</button>
            </div>

            <!-- Results -->
            <div v-if="discoveryResult" class="border border-border rounded-xl overflow-hidden">
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
                      <p class="text-sm font-display font-medium text-primary break-words">"{{ r.query }}"</p>
                      <div class="flex items-center gap-2 mt-1">
                        <span class="text-[11px] font-display uppercase tracking-wider px-1.5 py-0.5 rounded bg-warm-100 text-muted">{{ r.provider }}</span>
                        <span class="text-xs" :class="r.found ? 'text-score-good' : 'text-score-bad'">{{ r.found ? 'Found' : 'Not found' }}</span>
                      </div>
                      <p class="text-xs text-muted mt-1.5 leading-relaxed break-words" style="overflow-wrap: anywhere">{{ r.context }}</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </template>

          <!-- Non-Pro: teaser -->
          <template v-else>
            <div class="border border-accent/20 rounded-xl p-6 bg-accent/[0.03]">
              <p class="text-sm text-secondary mb-2 max-w-prose">
                With the AI Discovery Test, we query ChatGPT, Claude, and Perplexity with real queries and check if your site actually appears in the responses. See exactly where you are found and where you are not.
              </p>
              <p class="text-xs text-muted mb-4">Available on the Pro plan.</p>
              <router-link to="/pricing" class="btn-primary text-sm">Upgrade to Pro</router-link>
            </div>
          </template>
        </section>

        <!-- ─── ACTIONS ROW (Desktop) ─── -->
        <section class="border-t border-border-light pt-8 animate-slide-up" style="animation-delay: 200ms">
          <div class="flex flex-wrap gap-3">
            <button @click="shareReport" class="btn-secondary">
              <svg class="w-3.5 h-3.5 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
              </svg>
              {{ copied ? 'Link copied!' : 'Share report' }}
            </button>
            <router-link :to="{ name: 'Badge', params: { id: scanId } }" class="btn-secondary">
              <svg class="w-3.5 h-3.5 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
              </svg>
              Download badge
            </router-link>
            <router-link to="/" class="btn-secondary">
              <svg class="w-3.5 h-3.5 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
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
            <a href="https://github.com/lennystepn-hue/agentready" target="_blank" rel="noopener" class="hover:text-secondary transition-colors">GitHub</a>
          </div>
        </div>
      </footer>
    </div>

    <!-- ─── STICKY MOBILE BAR ─── -->
    <div v-if="scan" class="sm:hidden fixed bottom-0 inset-x-0 z-50 border-t border-border bg-surface/95 backdrop-blur-sm px-4 py-3 flex items-center gap-3">
      <template v-if="isLoggedIn && hasFixAccess">
        <button @click="handleDownloadFixes" :disabled="downloading" class="btn-primary flex-1">
          {{ downloading ? 'Downloading...' : 'Download Fix Files' }}
        </button>
      </template>
      <template v-else-if="isLoggedIn">
        <button @click="handlePurchaseFixFiles" :disabled="purchasing" class="btn-primary flex-1">
          {{ purchasing ? 'Redirecting...' : 'Get Fix Files — $9' }}
        </button>
      </template>
      <template v-else>
        <router-link :to="{ name: 'Login', query: { redirect: $route.fullPath } }" class="btn-primary flex-1 text-center">
          Get Fix Files
        </router-link>
      </template>
      <button @click="shareReport" class="btn-secondary px-3">
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
        </svg>
      </button>
    </div>
  </div>
</template>
