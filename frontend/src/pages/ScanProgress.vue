<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getScanResult } from '../api.js'
import CheckItem from '../components/CheckItem.vue'

const route = useRoute()
const router = useRouter()

const scanId = route.params.id
const scan = ref(null)
const error = ref('')
const progress = ref(0)
let pollTimer = null

const categories = [
  { key: 'Protocol Readiness', label: 'Protocol Readiness' },
  { key: 'Structured Data Quality', label: 'Structured Data Quality' },
  { key: 'Agent Accessibility', label: 'Agent Accessibility' },
  { key: 'Transaction Readiness', label: 'Transaction Readiness' },
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
      setTimeout(() => {
        router.push({ name: 'Report', params: { id: scanId } })
      }, 800)
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
  <div class="flex-1 flex flex-col">
    <!-- Nav -->
    <nav class="border-b border-border-light">
      <div class="max-w-5xl mx-auto px-6 lg:px-8 h-14 flex items-center">
        <router-link to="/" class="flex items-center gap-2">
          <svg class="w-5 h-5 text-accent" viewBox="0 0 24 24" fill="none">
            <path d="M12 2L4 20h4l1.5-4h5L16 20h4L12 2zm0 7l2 5h-4l2-5z" fill="currentColor"/>
            <path d="M20 8a10 10 0 00-4-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" opacity="0.5"/>
            <path d="M22 6a14 14 0 00-6-5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" opacity="0.3"/>
          </svg>
          <span class="font-display font-bold text-[15px] tracking-tight">AgentCheck</span>
        </router-link>
        <router-link to="/" class="btn-ghost text-[13px]">
          <svg class="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
          </svg>
          Back to home
        </router-link>
      </div>
    </nav>

    <!-- Content -->
    <div class="flex-1 flex items-start justify-center px-6 lg:px-8 py-16 sm:py-20">
      <div class="w-full max-w-md">

        <!-- Error state -->
        <div v-if="error" class="animate-fade-in">
          <h2 class="font-display text-xl font-bold mb-2 text-score-bad">Scan failed</h2>
          <p class="text-secondary mb-6 text-sm leading-relaxed">{{ error }}</p>
          <router-link to="/" class="btn-primary">Start a new scan</router-link>
        </div>

        <!-- Progress state -->
        <div v-else class="animate-fade-in">
          <!-- Domain prominent -->
          <div class="mb-8">
            <p class="section-label mb-1">Scanning</p>
            <h1 class="font-display text-xl font-bold text-primary">{{ domainDisplay }}</h1>
          </div>

          <!-- Thin progress bar -->
          <div class="mb-10">
            <div class="flex items-baseline justify-between mb-2">
              <span class="text-sm text-secondary">Progress</span>
              <span class="text-sm font-display font-semibold tabular-nums text-accent">{{ Math.round(progress) }}%</span>
            </div>
            <div class="h-1 bg-warm-200 rounded-full overflow-hidden">
              <div
                class="h-full bg-accent rounded-full transition-all duration-700 ease-out"
                :style="{ width: progress + '%' }"
              />
            </div>
          </div>

          <!-- Category checklist -->
          <div class="mb-8">
            <p class="section-label mb-3">Categories</p>
            <div class="border-t border-border-light">
              <CheckItem
                v-for="cat in categoryStatuses"
                :key="cat.key"
                :name="cat.label"
                :status="cat.status"
              />
            </div>
          </div>

          <!-- Live issues feed -->
          <div v-if="issues.length > 0">
            <p class="section-label mb-3">Issues found so far</p>
            <div class="border-t border-border-light stagger-children">
              <CheckItem
                v-for="(issue, idx) in issues"
                :key="idx"
                :name="issue.name"
                :status="issue.status"
                :message="issue.message"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
