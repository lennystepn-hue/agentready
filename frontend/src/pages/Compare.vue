<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { isLoggedIn, isPro, user, logout } from '../auth.js'
import { compareDomains } from '../api.js'
import ScoreCircle from '../components/ScoreCircle.vue'
import CategoryBar from '../components/CategoryBar.vue'
import AppLayout from '../components/AppLayout.vue'

const router = useRouter()

const yourDomain = ref('')
const competitors = ref(['', '', ''])
const results = ref(null)
const loading = ref(false)
const error = ref('')

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
            <div>
              <label class="block text-sm font-display font-medium text-primary mb-1.5">Your domain</label>
              <input
                v-model="yourDomain"
                type="text"
                placeholder="your-shop.com"
                class="input-field"
                :disabled="loading"
              />
            </div>
            <div v-for="(_, idx) in competitors" :key="idx">
              <label class="block text-sm font-display font-medium text-primary mb-1.5">Competitor {{ idx + 1 }}</label>
              <input
                v-model="competitors[idx]"
                type="text"
                :placeholder="`competitor-${idx + 1}.com`"
                class="input-field"
                :disabled="loading"
              />
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
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </AppLayout>
</template>
