<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { isLoggedIn, isPro, user, logout } from '../auth.js'
import { compareDomains, getUserScans } from '../api.js'
import ScoreCircle from '../components/ScoreCircle.vue'
import CategoryBar from '../components/CategoryBar.vue'
import AppLayout from '../components/AppLayout.vue'

const router = useRouter()
const route = useRoute()

const yourDomain = ref('')
const competitors = ref(['', '', ''])
const results = ref(null)
const loading = ref(false)
const error = ref('')
const allScans = ref([])
const focusedField = ref(null) // 'your' | 0 | 1 | 2
const resultsVisible = ref(false)

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

// Unique scanned domains (most recent first)
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

// Lookup scan_id by domain for linking to reports
const scanIdByDomain = computed(() => {
  const map = {}
  for (const s of allScans.value) {
    if (s.domain && s.scan_id && s.status === 'completed' && !map[s.domain]) {
      map[s.domain] = s.scan_id
    }
  }
  return map
})

// Winner: domain with highest score
const winnerDomain = computed(() => {
  if (!results.value || results.value.length === 0) return null
  let best = results.value[0]
  for (const r of results.value) {
    if ((r.score || 0) > (best.score || 0)) best = r
  }
  return best.domain
})

// All unique category keys across all results
const categoryKeys = computed(() => {
  if (!results.value) return []
  const keys = new Set()
  for (const r of results.value) {
    if (r.categories) {
      Object.keys(r.categories).forEach(k => keys.add(k))
    }
  }
  return Array.from(keys)
})

function suggestionsFor(fieldId) {
  const query = fieldId === 'your'
    ? yourDomain.value.trim().toLowerCase()
    : (competitors.value[fieldId] || '').trim().toLowerCase()

  return scannedDomains.value
    .filter(s => !query || s.domain.toLowerCase().includes(query))
    .slice(0, 5)
}

function selectSuggestion(fieldId, domain) {
  if (fieldId === 'your') {
    yourDomain.value = domain
  } else {
    competitors.value[fieldId] = domain
  }
  focusedField.value = null
}

function handleFocus(fieldId) {
  focusedField.value = fieldId
}

function handleBlur() {
  setTimeout(() => { focusedField.value = null }, 200)
}

async function handleCompare() {
  const domains = [yourDomain.value.trim(), ...competitors.value.map(c => c.trim())].filter(Boolean)
  if (domains.length < 2) {
    error.value = 'Please enter at least two domains to compare.'
    return
  }

  error.value = ''
  loading.value = true
  resultsVisible.value = false
  try {
    results.value = await compareDomains(domains)
    setTimeout(() => { resultsVisible.value = true }, 50)
  } catch (e) {
    error.value = e.message || 'Comparison failed. Please try again.'
  } finally {
    loading.value = false
  }
}

function scoreColorBorder(score) {
  if (score >= 70) return 'border-score-good'
  if (score >= 40) return 'border-score-medium'
  return 'border-score-bad'
}

function scoreColorClass(score) {
  if (score >= 70) return 'text-score-good'
  if (score >= 40) return 'text-score-medium'
  return 'text-score-bad'
}

function scoreDotClass(score) {
  if (score >= 70) return 'bg-score-good'
  if (score >= 40) return 'bg-score-medium'
  return 'bg-score-bad'
}

function categoryScoreFor(result, key) {
  if (!result.categories || !result.categories[key]) return null
  return result.categories[key].score ?? null
}

function categoryMaxFor(result, key) {
  if (!result.categories || !result.categories[key]) return 100
  return result.categories[key].max_score || result.categories[key].max || 100
}

// Bar width % for horizontal comparison bars
function barWidth(score, max) {
  if (!max || max === 0) return 0
  return Math.round((score / max) * 100)
}

onMounted(async () => {
  try {
    const data = await getUserScans()
    const raw = Array.isArray(data) ? data : (data.scans || [])
    allScans.value = raw.map(normalizeScan).sort((a, b) => new Date(b.created_at) - new Date(a.created_at))

    // Pre-fill from query params (e.g. from AI insights "Compare all" button)
    if (route.query.domains) {
      const domainList = route.query.domains.split(',')
      domainList.forEach((d, i) => {
        if (i === 0) {
          yourDomain.value = d
        } else if (i - 1 < competitors.value.length) {
          competitors.value[i - 1] = d
        }
      })
    } else if (!yourDomain.value && allScans.value.length > 0) {
      // Pre-fill the first domain with the most recently scanned domain
      yourDomain.value = allScans.value[0].domain
    }
  } catch {
    // non-critical
  }
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
              <h1 class="font-display text-2xl font-bold tracking-tight text-primary">Competitor comparison</h1>
              <p class="text-sm text-secondary mt-1.5 max-w-md leading-relaxed">
                See where you lead and where competitors outrank you. Enter up to 4 domains side-by-side.
              </p>
            </div>
          </div>
        </div>

        <!-- Pro gate -->
        <div v-if="!isPro" class="border-l-4 border-accent rounded-r-lg p-6 bg-accent/[0.03] animate-slide-up">
          <h3 class="font-display font-semibold text-primary mb-1">Unlock competitor comparison</h3>
          <p class="text-sm text-secondary mb-4 max-w-sm">
            See how your AI agent readiness stacks up against your competitors. Available on Pro.
          </p>
          <router-link to="/pricing" class="btn-primary">Upgrade to Pro</router-link>
        </div>

        <!-- Compare form + results -->
        <div v-else class="animate-slide-up">

          <!-- Input form — unified pill layout -->
          <div class="mb-10">
            <form @submit.prevent="handleCompare">
              <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 mb-4">

                <!-- Your domain -->
                <div class="relative">
                  <label class="block text-[11px] font-display font-semibold text-muted uppercase tracking-wider mb-1.5">Your site</label>
                  <div class="relative">
                    <span class="absolute inset-y-0 left-3 flex items-center pointer-events-none">
                      <svg class="w-3.5 h-3.5 text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
                      </svg>
                    </span>
                    <input
                      v-model="yourDomain"
                      type="text"
                      placeholder="your-shop.com"
                      class="input-field pl-8 text-sm transition-all focus:ring-2 focus:ring-accent/40 focus:border-accent"
                      :disabled="loading"
                      @focus="handleFocus('your')"
                      @blur="handleBlur"
                      @input="focusedField = 'your'"
                    />
                  </div>
                  <!-- Suggestions dropdown -->
                  <div
                    v-if="focusedField === 'your' && suggestionsFor('your').length > 0"
                    class="absolute z-20 left-0 right-0 top-full mt-1 border border-border rounded-lg bg-surface shadow-lg overflow-hidden"
                  >
                    <button
                      v-for="s in suggestionsFor('your')"
                      :key="s.domain"
                      type="button"
                      @mousedown.prevent="selectSuggestion('your', s.domain)"
                      class="w-full text-left px-3 py-2 text-sm hover:bg-warm-50 transition-colors flex items-center justify-between gap-2"
                    >
                      <span class="font-display text-primary truncate text-[13px]">{{ s.domain }}</span>
                      <span v-if="s.score != null" class="flex items-center gap-1 shrink-0">
                        <span class="w-1.5 h-1.5 rounded-full shrink-0" :class="scoreDotClass(s.score)"></span>
                        <span class="text-xs font-display font-semibold tabular-nums" :class="scoreColorClass(s.score)">{{ s.score }}</span>
                      </span>
                    </button>
                  </div>
                </div>

                <!-- Competitor domains -->
                <div v-for="(_, idx) in competitors" :key="idx" class="relative">
                  <label class="block text-[11px] font-display font-semibold text-muted uppercase tracking-wider mb-1.5">Competitor {{ idx + 1 }}</label>
                  <div class="relative">
                    <span class="absolute inset-y-0 left-3 flex items-center pointer-events-none">
                      <svg class="w-3.5 h-3.5 text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
                      </svg>
                    </span>
                    <input
                      v-model="competitors[idx]"
                      type="text"
                      :placeholder="`competitor-${idx + 1}.com`"
                      class="input-field pl-8 text-sm transition-all focus:ring-2 focus:ring-accent/40 focus:border-accent"
                      :disabled="loading"
                      @focus="handleFocus(idx)"
                      @blur="handleBlur"
                      @input="focusedField = idx"
                    />
                  </div>
                  <!-- Suggestions dropdown -->
                  <div
                    v-if="focusedField === idx && suggestionsFor(idx).length > 0"
                    class="absolute z-20 left-0 right-0 top-full mt-1 border border-border rounded-lg bg-surface shadow-lg overflow-hidden"
                  >
                    <button
                      v-for="s in suggestionsFor(idx)"
                      :key="s.domain"
                      type="button"
                      @mousedown.prevent="selectSuggestion(idx, s.domain)"
                      class="w-full text-left px-3 py-2 text-sm hover:bg-warm-50 transition-colors flex items-center justify-between gap-2"
                    >
                      <span class="font-display text-primary truncate text-[13px]">{{ s.domain }}</span>
                      <span v-if="s.score != null" class="flex items-center gap-1 shrink-0">
                        <span class="w-1.5 h-1.5 rounded-full shrink-0" :class="scoreDotClass(s.score)"></span>
                        <span class="text-xs font-display font-semibold tabular-nums" :class="scoreColorClass(s.score)">{{ s.score }}</span>
                      </span>
                    </button>
                  </div>
                </div>
              </div>

              <div class="flex items-center gap-3">
                <button
                  type="submit"
                  class="btn-primary"
                  :disabled="loading || !yourDomain.trim()"
                >
                  <svg v-if="loading" class="w-3.5 h-3.5 mr-2 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  {{ loading ? 'Comparing...' : 'Run comparison' }}
                </button>
                <p v-if="error" class="text-sm text-score-bad">{{ error }}</p>
              </div>
            </form>
          </div>

          <!-- Empty state -->
          <div v-if="!results && !loading" class="border border-border-light rounded-lg p-10 text-center bg-warm-50">
            <div class="w-10 h-10 rounded-full bg-accent/10 flex items-center justify-center mx-auto mb-3">
              <svg class="w-5 h-5 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7m0 10a2 2 0 002 2h2a2 2 0 002-2V7a2 2 0 00-2-2h-2a2 2 0 00-2 2" />
              </svg>
            </div>
            <p class="font-display font-semibold text-primary text-sm mb-1">Compare your site against competitors</p>
            <p class="text-sm text-secondary">Enter up to 4 domains above and run the comparison to see how you stack up.</p>
          </div>

          <!-- Results -->
          <div v-if="results && results.length > 0" :class="['transition-all duration-500', resultsVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4']">

            <!-- Score overview row -->
            <div class="mb-2 flex items-center justify-between">
              <p class="section-label">Results — {{ results.length }} domains</p>
              <p v-if="winnerDomain" class="text-xs text-score-good font-display font-semibold">
                {{ winnerDomain }} leads
              </p>
            </div>

            <!-- Score circles + domain headers -->
            <div class="grid gap-3 mb-6" :class="{
              'grid-cols-2': results.length === 2,
              'grid-cols-3': results.length === 3,
              'grid-cols-2 lg:grid-cols-4': results.length === 4,
            }">
              <div
                v-for="(r, idx) in results"
                :key="idx"
                class="relative border rounded-lg p-5 bg-surface transition-all duration-300"
                :class="[
                  r.domain === winnerDomain ? 'border-accent/50 bg-accent/[0.02]' : 'border-border',
                  resultsVisible ? `opacity-100 translate-y-0` : 'opacity-0 translate-y-3'
                ]"
                :style="{ transitionDelay: `${idx * 80}ms` }"
              >
                <!-- Winner badge -->
                <div v-if="r.domain === winnerDomain" class="absolute -top-2.5 left-4">
                  <span class="text-[10px] font-display font-semibold bg-accent text-white px-2 py-0.5 rounded-full">Leader</span>
                </div>

                <!-- Your site badge -->
                <div v-else-if="idx === 0" class="absolute -top-2.5 left-4">
                  <span class="text-[10px] font-display font-semibold bg-warm-700 text-white px-2 py-0.5 rounded-full">Your site</span>
                </div>

                <div class="flex flex-col items-center text-center gap-3 mb-4">
                  <ScoreCircle :score="r.score || 0" :grade="r.grade || ''" :size="64" />
                  <div class="min-w-0">
                    <p class="text-sm font-display font-semibold text-primary break-all leading-tight">{{ r.domain }}</p>
                    <p class="text-xs text-muted mt-0.5">Score {{ r.score || 0 }}/100</p>
                  </div>
                </div>

                <!-- View report link -->
                <div class="border-t border-border-light pt-3 text-center">
                  <router-link
                    v-if="scanIdByDomain[r.domain]"
                    :to="{ name: 'Report', params: { id: scanIdByDomain[r.domain] } }"
                    class="text-[12px] text-accent hover:text-accent-hover font-display font-medium transition-colors"
                  >
                    View full report &rarr;
                  </router-link>
                  <span v-else class="text-[12px] text-muted">No report available</span>
                </div>
              </div>
            </div>

            <!-- Category comparison — horizontal bar chart -->
            <div v-if="categoryKeys.length > 0" class="border border-border rounded-lg overflow-hidden bg-surface">
              <div class="px-5 py-3.5 border-b border-border-light bg-warm-50 flex items-center justify-between">
                <p class="section-label">Category breakdown</p>
                <!-- Legend -->
                <div class="flex items-center gap-4 flex-wrap justify-end">
                  <div
                    v-for="(r, idx) in results"
                    :key="idx"
                    class="flex items-center gap-1.5"
                  >
                    <span
                      class="w-2 h-2 rounded-full shrink-0"
                      :class="scoreDotClass(r.score || 0)"
                    ></span>
                    <span class="text-[11px] font-display text-secondary truncate max-w-[80px]">{{ r.domain }}</span>
                  </div>
                </div>
              </div>

              <div class="divide-y divide-border-light">
                <div
                  v-for="key in categoryKeys"
                  :key="key"
                  class="px-5 py-4"
                >
                  <p class="text-[13px] font-display font-semibold text-primary mb-3 capitalize">{{ key.replace(/_/g, ' ') }}</p>
                  <div class="space-y-2">
                    <div
                      v-for="(r, idx) in results"
                      :key="idx"
                      class="flex items-center gap-3"
                    >
                      <!-- Domain label -->
                      <span class="text-[11px] font-display text-muted w-28 truncate shrink-0">{{ r.domain }}</span>
                      <!-- Bar track -->
                      <div class="flex-1 h-2 bg-warm-100 rounded-full overflow-hidden">
                        <div
                          class="h-full rounded-full transition-all duration-700 ease-out"
                          :class="[
                            categoryScoreFor(r, key) !== null
                              ? (categoryScoreFor(r, key) >= 70 ? 'bg-score-good' : categoryScoreFor(r, key) >= 40 ? 'bg-score-medium' : 'bg-score-bad')
                              : 'bg-warm-200'
                          ]"
                          :style="{ width: resultsVisible && categoryScoreFor(r, key) !== null ? barWidth(categoryScoreFor(r, key), categoryMaxFor(r, key)) + '%' : '0%' }"
                        ></div>
                      </div>
                      <!-- Score label -->
                      <span
                        class="text-[12px] font-display font-semibold tabular-nums w-10 text-right shrink-0"
                        :class="categoryScoreFor(r, key) !== null ? scoreColorClass(categoryScoreFor(r, key)) : 'text-muted'"
                      >
                        {{ categoryScoreFor(r, key) !== null ? categoryScoreFor(r, key) : '—' }}
                      </span>
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
