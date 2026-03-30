<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getScanResult } from '../api.js'
import AppHeader from '../components/AppHeader.vue'
import CheckItem from '../components/CheckItem.vue'

const route = useRoute()
const router = useRouter()

const scanId = route.params.id
const scan = ref(null)
const error = ref('')
const progress = ref(0)
const showCompletion = ref(false)
const finalScore = ref(0)
let pollTimer = null

const categories = [
  { key: 'Protocol Readiness', label: 'Protocol Readiness' },
  { key: 'Structured Data Quality', label: 'Structured Data Quality' },
  { key: 'Agent Accessibility', label: 'Agent Accessibility' },
  { key: 'Conversion Readiness', label: 'Conversion Readiness' },
  { key: 'Trust Signals', label: 'Trust Signals' },
]

const domainDisplay = computed(() => {
  if (!scan.value?.domain) return '...'
  return scan.value.domain
})

const categoryStatuses = computed(() => {
  if (!scan.value) {
    return categories.map((c, i) => ({
      ...c,
      status: i === 0 ? 'running' : 'waiting',
    }))
  }

  const p = progress.value
  return categories.map((c, i) => {
    const threshold = ((i + 1) / categories.length) * 100
    const step = 100 / categories.length
    if (p >= threshold) return { ...c, status: 'pass' }
    if (p >= threshold - step) return { ...c, status: 'running' }
    return { ...c, status: 'waiting' }
  })
})

const issues = ref([])

const scoreLabel = computed(() => {
  const s = finalScore.value
  if (s >= 80) return { text: 'Excellent', color: 'text-score-good' }
  if (s >= 60) return { text: 'Good', color: 'text-score-medium' }
  if (s >= 40) return { text: 'Needs work', color: 'text-score-medium' }
  return { text: 'Critical', color: 'text-score-bad' }
})

async function poll() {
  try {
    const result = await getScanResult(scanId)
    scan.value = result

    if (result.status === 'completed') {
      progress.value = 100
    } else if (result.status === 'running') {
      progress.value = Math.min(progress.value + 15, 90)
    }

    if (result.checks && result.checks.length > 0) {
      issues.value = result.checks
        .filter(c => c.status === 'fail' || c.status === 'warn')
        .slice(0, 8)
    }

    if (result.status === 'completed') {
      clearInterval(pollTimer)
      // Extract score from result if available
      if (result.score != null) finalScore.value = result.score
      showCompletion.value = true
      setTimeout(() => {
        router.push({ name: 'Report', params: { id: scanId } })
      }, 1800)
    } else if (result.status === 'failed') {
      clearInterval(pollTimer)
      error.value = result.error || 'The scan has failed. Please try again.'
    }
  } catch (e) {
    error.value = e.message || 'Connection error. Please check your network.'
    clearInterval(pollTimer)
  }
}

onMounted(() => {
  poll()
  pollTimer = setInterval(poll, 2000)
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})
</script>

<template>
  <div class="flex-1 flex flex-col bg-grid">
    <AppHeader show-back="/" back-label="Home" />

    <div class="flex-1 flex items-start justify-center px-6 lg:px-8 py-14 sm:py-20">
      <div class="w-full max-w-md">

        <!-- Error state -->
        <div v-if="error" class="animate-fade-in">
          <div class="w-10 h-10 rounded-full bg-score-bad/10 flex items-center justify-center mb-5">
            <svg class="w-5 h-5 text-score-bad" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </div>
          <h2 class="font-display text-xl font-bold mb-2 text-primary">Scan failed</h2>
          <p class="text-secondary mb-6 text-sm leading-relaxed">{{ error }}</p>
          <router-link to="/" class="btn-primary">Start a new scan</router-link>
        </div>

        <!-- Completion overlay -->
        <div
          v-else-if="showCompletion"
          class="text-center animate-fade-in"
        >
          <!-- Score reveal -->
          <div class="flex flex-col items-center gap-4 mb-6">
            <div class="w-20 h-20 rounded-full bg-accent/10 flex items-center justify-center scale-in-bounce">
              <svg class="w-9 h-9 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <div>
              <p class="section-label mb-1">Scan complete</p>
              <h1 class="font-display text-2xl font-bold text-primary">{{ domainDisplay }}</h1>
            </div>
          </div>
          <p class="text-sm text-secondary">Loading your full report&hellip;</p>
          <div class="mt-4 h-0.5 bg-warm-100 rounded-full overflow-hidden mx-auto w-24">
            <div class="h-full bg-accent rounded-full animate-progress-indeterminate"></div>
          </div>
        </div>

        <!-- Progress state -->
        <div v-else class="animate-fade-in">

          <!-- Domain header -->
          <div class="mb-8">
            <p class="section-label mb-1.5">Scanning</p>
            <h1 class="font-display text-xl font-bold text-primary overflow-wrap-anywhere">{{ domainDisplay }}</h1>
            <p class="text-[13px] text-muted mt-1.5">Usually completes in ~20 seconds</p>
          </div>

          <!-- Progress bar with shimmer -->
          <div class="mb-10">
            <div class="flex items-baseline justify-between mb-2">
              <span class="text-[13px] text-secondary">Progress</span>
              <span class="text-[13px] font-display font-semibold tabular-nums text-accent">{{ Math.round(progress) }}%</span>
            </div>
            <div class="h-1.5 bg-warm-200 rounded-full overflow-hidden">
              <div
                class="h-full bg-accent rounded-full transition-all duration-700 ease-out relative overflow-hidden"
                :style="{ width: progress + '%' }"
              >
                <!-- Shimmer on leading edge -->
                <div class="absolute inset-0 progress-shimmer" aria-hidden="true"></div>
              </div>
            </div>
          </div>

          <!-- Category checklist with connecting line -->
          <div class="mb-8">
            <p class="section-label mb-4">Categories</p>
            <div class="relative">
              <!-- Left border connecting line -->
              <div class="absolute left-[8px] top-3 bottom-3 w-px bg-warm-200" aria-hidden="true"></div>

              <div class="space-y-0">
                <div
                  v-for="(cat, i) in categoryStatuses"
                  :key="cat.key"
                  class="flex items-center gap-3 py-2.5 relative"
                  :class="{ 'animate-fade-in': cat.status === 'pass' }"
                  :style="cat.status === 'pass' ? { animationDelay: `${i * 40}ms` } : {}"
                >
                  <!-- Status dot/indicator -->
                  <div class="flex-shrink-0 relative z-10">
                    <!-- Completed: checkmark with scale-in -->
                    <div
                      v-if="cat.status === 'pass'"
                      class="w-[18px] h-[18px] rounded-full bg-score-good flex items-center justify-center check-scale-in"
                    >
                      <svg class="w-2.5 h-2.5 text-white" fill="none" viewBox="0 0 10 10" stroke="currentColor" stroke-width="2">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M2 5.5l2 2 4-4" />
                      </svg>
                    </div>
                    <!-- Running: pulsing accent dot -->
                    <div v-else-if="cat.status === 'running'" class="relative w-[18px] h-[18px] flex items-center justify-center">
                      <span class="absolute w-[18px] h-[18px] rounded-full bg-accent/20 animate-ping"></span>
                      <span class="w-2.5 h-2.5 rounded-full bg-accent"></span>
                    </div>
                    <!-- Waiting: dashed circle -->
                    <svg v-else class="w-[18px] h-[18px] text-warm-300" viewBox="0 0 18 18" fill="none">
                      <circle cx="9" cy="9" r="7" stroke="currentColor" stroke-width="1" stroke-dasharray="3 3" />
                    </svg>
                  </div>

                  <!-- Label -->
                  <span
                    class="text-sm transition-colors duration-300"
                    :class="cat.status === 'waiting' ? 'text-muted' : cat.status === 'running' ? 'text-accent font-display font-medium' : 'text-primary'"
                  >
                    {{ cat.label }}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <!-- Live issues feed as inline pills -->
          <div v-if="issues.length > 0" class="animate-fade-in">
            <p class="section-label mb-3">Issues found so far</p>
            <div class="flex flex-wrap gap-2">
              <span
                v-for="(issue, idx) in issues"
                :key="idx"
                class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-display font-medium animate-fade-in"
                :style="{ animationDelay: `${idx * 50}ms` }"
                :class="issue.status === 'fail'
                  ? 'bg-score-bad/8 text-score-bad border border-score-bad/20'
                  : 'bg-score-medium/8 text-score-medium border border-score-medium/20'"
              >
                <span
                  class="w-1.5 h-1.5 rounded-full flex-shrink-0"
                  :class="issue.status === 'fail' ? 'bg-score-bad' : 'bg-score-medium'"
                ></span>
                {{ issue.name }}
              </span>
            </div>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>

<style scoped>
/* Shimmer sweep on the progress bar leading edge */
.progress-shimmer {
  background: linear-gradient(
    90deg,
    transparent 0%,
    rgba(255, 255, 255, 0.35) 50%,
    transparent 100%
  );
  animation: shimmerSweep 1.6s ease-in-out infinite;
}

@keyframes shimmerSweep {
  0%   { transform: translateX(-100%); }
  100% { transform: translateX(200%); }
}

/* Checkmark scale-in when category completes */
.check-scale-in {
  animation: checkScaleIn 0.28s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
}

@keyframes checkScaleIn {
  from { transform: scale(0); opacity: 0; }
  to   { transform: scale(1); opacity: 1; }
}

/* Score reveal bounce */
.scale-in-bounce {
  animation: scaleInBounce 0.5s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
}

@keyframes scaleInBounce {
  from { transform: scale(0.4); opacity: 0; }
  to   { transform: scale(1); opacity: 1; }
}

/* Indeterminate progress for completion loading bar */
.animate-progress-indeterminate {
  width: 40%;
  animation: progressIndeterminate 1.2s ease-in-out infinite;
}

@keyframes progressIndeterminate {
  0%   { transform: translateX(-150%); }
  100% { transform: translateX(350%); }
}
</style>
