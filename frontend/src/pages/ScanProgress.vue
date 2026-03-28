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
  { key: 'protocol_readiness', label: 'Protokoll-Erkennung' },
  { key: 'structured_data', label: 'Strukturierte Daten' },
  { key: 'agent_accessibility', label: 'Agent-Zugänglichkeit' },
  { key: 'transaction_readiness', label: 'Transaktions-Bereitschaft' },
  { key: 'trust_signals', label: 'Vertrauens-Signale' },
]

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
    if (p >= threshold) return { ...c, status: 'passed' }
    if (p >= threshold - (100 / categories.length)) return { ...c, status: 'running' }
    return { ...c, status: 'waiting' }
  })
})

const issues = ref([])

async function poll() {
  try {
    const result = await getScanResult(scanId)
    scan.value = result

    // Update progress
    if (result.progress !== undefined) {
      progress.value = result.progress
    } else if (result.status === 'completed') {
      progress.value = 100
    }

    // Collect issues from checks
    if (result.checks) {
      issues.value = result.checks
        .filter(c => c.status === 'failed' || c.status === 'warning')
        .slice(0, 10)
    }

    if (result.status === 'completed') {
      clearInterval(pollTimer)
      // Brief pause to show 100%, then redirect
      setTimeout(() => {
        router.push({ name: 'Report', params: { id: scanId } })
      }, 800)
    } else if (result.status === 'failed') {
      clearInterval(pollTimer)
      error.value = result.error || 'Der Scan ist fehlgeschlagen.'
    }
  } catch (e) {
    error.value = e.message || 'Verbindungsfehler.'
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
    <nav class="border-b border-slate-800/50">
      <div class="max-w-6xl mx-auto px-6 h-16 flex items-center">
        <router-link to="/" class="flex items-center gap-2">
          <div class="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center">
            <svg class="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <span class="font-bold text-lg">AgentReady</span>
        </router-link>
      </div>
    </nav>

    <!-- Content -->
    <div class="flex-1 flex items-center justify-center px-6 py-16">
      <div class="w-full max-w-lg">
        <!-- Error state -->
        <div v-if="error" class="text-center">
          <div class="w-16 h-16 rounded-full bg-red-500/10 flex items-center justify-center mx-auto mb-4">
            <svg class="w-8 h-8 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </div>
          <h2 class="text-xl font-bold mb-2">Scan fehlgeschlagen</h2>
          <p class="text-slate-400 mb-6">{{ error }}</p>
          <router-link to="/" class="btn-primary">Neuer Scan</router-link>
        </div>

        <!-- Progress state -->
        <div v-else class="animate-fade-in">
          <div class="text-center mb-8">
            <h2 class="text-xl font-bold mb-1">Scan läuft...</h2>
            <p class="text-sm text-slate-400">Deine Website wird analysiert</p>
          </div>

          <!-- Progress bar -->
          <div class="mb-8">
            <div class="flex items-center justify-between mb-2">
              <span class="text-sm text-slate-400">Fortschritt</span>
              <span class="text-sm font-semibold tabular-nums text-blue-400">{{ Math.round(progress) }}%</span>
            </div>
            <div class="h-2 bg-slate-800 rounded-full overflow-hidden">
              <div
                class="h-full bg-blue-500 rounded-full transition-all duration-700 ease-out"
                :style="{ width: progress + '%' }"
              />
            </div>
          </div>

          <!-- Category checklist -->
          <div class="card mb-6">
            <h3 class="text-sm font-semibold text-slate-300 mb-3 uppercase tracking-wider">Kategorien</h3>
            <div class="divide-y divide-slate-800/50">
              <CheckItem
                v-for="cat in categoryStatuses"
                :key="cat.key"
                :name="cat.label"
                :status="cat.status"
              />
            </div>
          </div>

          <!-- Live issues feed -->
          <div v-if="issues.length > 0" class="card">
            <h3 class="text-sm font-semibold text-slate-300 mb-3 uppercase tracking-wider">Gefundene Probleme</h3>
            <div class="space-y-1">
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
