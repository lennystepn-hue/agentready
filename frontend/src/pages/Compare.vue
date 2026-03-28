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
  try {
    results.value = await compareDomains(domains)
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

        <div class="animate-fade-in mb-8">
          <p class="section-label mb-2">Pro feature</p>
          <h1 class="font-display text-2xl font-bold tracking-tight text-primary">Competitor comparison</h1>
          <p class="text-sm text-secondary mt-2 leading-relaxed max-w-lg">
            Compare your AI agent readiness score against up to 3 competitors. See where you lead and where you need to catch up.
          </p>
        </div>

        <!-- Pro gate -->
        <div v-if="!isPro" class="border border-accent/20 rounded-lg p-8 bg-accent/[0.03] text-center animate-slide-up">
          <h3 class="font-display font-semibold text-primary mb-2">Pro feature</h3>
          <p class="text-sm text-secondary mb-4 max-w-sm mx-auto">
            Competitor comparison is available on the Pro plan. Upgrade to see how your shop stacks up.
          </p>
          <router-link to="/pricing" class="btn-primary">Upgrade to Pro</router-link>
        </div>

        <!-- Compare form -->
        <div v-else class="animate-slide-up">
          <form @submit.prevent="handleCompare" class="space-y-4 max-w-md mb-10">
            <!-- Your domain -->
            <div class="relative">
              <label class="block text-sm font-display font-medium text-primary mb-1.5">Your domain</label>
              <input
                v-model="yourDomain"
                type="text"
                placeholder="your-shop.com"
                class="input-field"
                :disabled="loading"
                @focus="handleFocus('your')"
                @blur="handleBlur"
                @input="focusedField = 'your'"
              />
              <div
                v-if="focusedField === 'your' && suggestionsFor('your').length > 0"
                class="absolute z-10 left-0 right-0 top-full mt-1 border border-border rounded-lg bg-surface shadow-lg overflow-hidden"
              >
                <button
                  v-for="s in suggestionsFor('your')"
                  :key="s.domain"
                  type="button"
                  @mousedown.prevent="selectSuggestion('your', s.domain)"
                  class="w-full text-left px-4 py-2.5 text-sm hover:bg-warm-100 transition-colors flex items-center justify-between gap-3"
                >
                  <span class="font-display text-primary truncate">{{ s.domain }}</span>
                  <span v-if="s.score != null" class="text-xs font-display font-semibold tabular-nums shrink-0" :class="scoreColorClass(s.score)">
                    {{ s.score }}
                  </span>
                </button>
              </div>
            </div>

            <!-- Competitor domains -->
            <div v-for="(_, idx) in competitors" :key="idx" class="relative">
              <label class="block text-sm font-display font-medium text-primary mb-1.5">Competitor {{ idx + 1 }}</label>
              <input
                v-model="competitors[idx]"
                type="text"
                :placeholder="`competitor-${idx + 1}.com`"
                class="input-field"
                :disabled="loading"
                @focus="handleFocus(idx)"
                @blur="handleBlur"
                @input="focusedField = idx"
              />
              <div
                v-if="focusedField === idx && suggestionsFor(idx).length > 0"
                class="absolute z-10 left-0 right-0 top-full mt-1 border border-border rounded-lg bg-surface shadow-lg overflow-hidden"
              >
                <button
                  v-for="s in suggestionsFor(idx)"
                  :key="s.domain"
                  type="button"
                  @mousedown.prevent="selectSuggestion(idx, s.domain)"
                  class="w-full text-left px-4 py-2.5 text-sm hover:bg-warm-100 transition-colors flex items-center justify-between gap-3"
                >
                  <span class="font-display text-primary truncate">{{ s.domain }}</span>
                  <span v-if="s.score != null" class="text-xs font-display font-semibold tabular-nums shrink-0" :class="scoreColorClass(s.score)">
                    {{ s.score }}
                  </span>
                </button>
              </div>
            </div>

            <p v-if="error" class="text-sm text-score-bad">{{ error }}</p>

            <button
              type="submit"
              class="btn-primary"
              :disabled="loading || !yourDomain.trim()"
            >
              <svg v-if="loading" class="w-4 h-4 mr-2 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              {{ loading ? 'Comparing...' : 'Compare' }}
            </button>
          </form>

          <!-- Results -->
          <div v-if="results && results.length > 0" class="animate-slide-up">
            <p class="section-label mb-4">Results</p>
            <div class="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <div
                v-for="(r, idx) in results"
                :key="idx"
                class="border rounded-lg p-5 bg-surface transition-colors"
                :class="idx === 0 ? 'border-accent/40 bg-accent/[0.02]' : 'border-border'"
              >
                <div class="flex items-center gap-3 mb-4">
                  <ScoreCircle :score="r.score || 0" :grade="r.grade || ''" :size="56" />
                  <div class="min-w-0">
                    <p class="text-sm font-display font-semibold text-primary truncate">{{ r.domain }}</p>
                    <p v-if="idx === 0" class="text-[11px] text-accent font-display font-semibold">Your shop</p>
                  </div>
                </div>
                <div v-if="r.categories" class="space-y-3">
                  <CategoryBar
                    v-for="(cat, key) in r.categories"
                    :key="key"
                    :name="key"
                    :score="cat.score || 0"
                    :max-score="cat.max_score || cat.max || 100"
                  />
                </div>
                <div class="mt-4 pt-3 border-t border-border-light">
                  <router-link
                    v-if="scanIdByDomain[r.domain]"
                    :to="{ name: 'Report', params: { id: scanIdByDomain[r.domain] } }"
                    class="text-[13px] text-accent hover:text-accent-hover transition-colors"
                  >
                    View full report
                  </router-link>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </AppLayout>
</template>
