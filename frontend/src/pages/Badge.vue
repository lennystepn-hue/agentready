<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { getScanResult } from '../api.js'
import ScoreCircle from '../components/ScoreCircle.vue'

const route = useRoute()
const scanId = route.params.id

const scan = ref(null)
const loading = ref(true)
const error = ref('')
const copiedEmbed = ref(false)
const copiedMarkdown = ref(false)

const badgeUrl = computed(() => {
  if (!scan.value) return ''
  const origin = window.location.origin
  return `${origin}/api/badge/${scanId}.svg`
})

const embedCode = computed(() => {
  if (!scan.value) return ''
  const pageUrl = `${window.location.origin}/report/${scanId}`
  return `<a href="${pageUrl}" target="_blank" rel="noopener">
  <img src="${badgeUrl.value}" alt="AgentReady Score: ${scan.value.score}" width="200" />
</a>`
})

const markdownCode = computed(() => {
  if (!scan.value) return ''
  const pageUrl = `${window.location.origin}/report/${scanId}`
  return `[![AgentReady Score: ${scan.value.score}](${badgeUrl.value})](${pageUrl})`
})

const scoreColor = computed(() => {
  if (!scan.value) return '#3B82F6'
  if (scan.value.score >= 70) return '#22c55e'
  if (scan.value.score >= 40) return '#eab308'
  return '#ef4444'
})

const gradeLabel = computed(() => {
  if (!scan.value) return ''
  const s = scan.value.score
  if (s >= 90) return 'A+'
  if (s >= 80) return 'A'
  if (s >= 70) return 'B'
  if (s >= 60) return 'C'
  if (s >= 40) return 'D'
  return 'F'
})

function copyText(text, flag) {
  navigator.clipboard.writeText(text).then(() => {
    if (flag === 'embed') {
      copiedEmbed.value = true
      setTimeout(() => { copiedEmbed.value = false }, 2000)
    } else {
      copiedMarkdown.value = true
      setTimeout(() => { copiedMarkdown.value = false }, 2000)
    }
  })
}

async function fetchData() {
  try {
    scan.value = await getScanResult(scanId)
  } catch (e) {
    error.value = e.message || 'Badge konnte nicht geladen werden.'
  } finally {
    loading.value = false
  }
}

onMounted(fetchData)
</script>

<template>
  <div class="flex-1 flex flex-col">
    <!-- Nav -->
    <nav class="border-b border-slate-800/50">
      <div class="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
        <router-link to="/" class="flex items-center gap-2">
          <div class="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center">
            <svg class="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <span class="font-bold text-lg">AgentReady</span>
        </router-link>
        <router-link
          :to="{ name: 'Report', params: { id: scanId } }"
          class="text-sm text-slate-400 hover:text-slate-200 transition-colors"
        >
          Zurück zum Bericht
        </router-link>
      </div>
    </nav>

    <!-- Loading -->
    <div v-if="loading" class="flex-1 flex items-center justify-center">
      <svg class="w-8 h-8 text-blue-500 animate-spin" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
      </svg>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="flex-1 flex items-center justify-center px-6">
      <div class="text-center">
        <p class="text-slate-400 mb-4">{{ error }}</p>
        <router-link to="/" class="btn-primary">Startseite</router-link>
      </div>
    </div>

    <!-- Badge content -->
    <div v-else-if="scan" class="flex-1 px-6 py-16">
      <div class="max-w-2xl mx-auto">
        <div class="text-center mb-12 animate-fade-in">
          <h1 class="text-2xl font-bold mb-2">Dein AgentReady Badge</h1>
          <p class="text-slate-400">Zeige deinen Score auf deiner Website oder in deinem README.</p>
        </div>

        <!-- Badge Preview -->
        <div class="card flex items-center justify-center py-12 mb-8 animate-slide-up">
          <!-- Inline SVG badge preview -->
          <div class="bg-slate-950 border border-slate-700 rounded-xl px-6 py-4 flex items-center gap-4">
            <ScoreCircle :score="scan.score" :size="64" />
            <div>
              <div class="text-sm font-bold text-slate-200">AgentReady</div>
              <div class="text-xs text-slate-400">{{ scan.domain }}</div>
              <div class="text-lg font-bold mt-0.5" :style="{ color: scoreColor }">
                {{ scan.score }}/100 &middot; {{ gradeLabel }}
              </div>
            </div>
          </div>
        </div>

        <!-- Embed Code (HTML) -->
        <div class="mb-6 animate-slide-up" style="animation-delay: 100ms">
          <div class="flex items-center justify-between mb-2">
            <h2 class="text-sm font-semibold text-slate-300 uppercase tracking-wider">HTML Embed-Code</h2>
            <button
              @click="copyText(embedCode, 'embed')"
              class="text-xs text-slate-500 hover:text-slate-300 transition-colors"
            >
              {{ copiedEmbed ? 'Kopiert!' : 'Kopieren' }}
            </button>
          </div>
          <div class="bg-slate-950 border border-slate-800 rounded-lg p-4 overflow-x-auto">
            <pre class="text-sm text-slate-400"><code>{{ embedCode }}</code></pre>
          </div>
        </div>

        <!-- Markdown Code -->
        <div class="mb-6 animate-slide-up" style="animation-delay: 200ms">
          <div class="flex items-center justify-between mb-2">
            <h2 class="text-sm font-semibold text-slate-300 uppercase tracking-wider">Markdown</h2>
            <button
              @click="copyText(markdownCode, 'markdown')"
              class="text-xs text-slate-500 hover:text-slate-300 transition-colors"
            >
              {{ copiedMarkdown ? 'Kopiert!' : 'Kopieren' }}
            </button>
          </div>
          <div class="bg-slate-950 border border-slate-800 rounded-lg p-4 overflow-x-auto">
            <pre class="text-sm text-slate-400"><code>{{ markdownCode }}</code></pre>
          </div>
        </div>

        <!-- Back to report -->
        <div class="text-center mt-10 animate-slide-up" style="animation-delay: 300ms">
          <router-link
            :to="{ name: 'Report', params: { id: scanId } }"
            class="btn-secondary"
          >
            Zurück zum Bericht
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>
