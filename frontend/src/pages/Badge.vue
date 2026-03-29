<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { getScanResult } from '../api.js'
import AppHeader from '../components/AppHeader.vue'
import ScoreCircle from '../components/ScoreCircle.vue'
import CodeBlock from '../components/CodeBlock.vue'

const route = useRoute()
const scanId = route.params.id

const scan = ref(null)
const loading = ref(true)
const error = ref('')

const badgeUrl = computed(() => {
  if (!scan.value) return ''
  return `${window.location.origin}/api/badge/${scanId}.svg`
})

const reportUrl = computed(() => {
  return `${window.location.origin}/report/${scanId}`
})

const embedCode = computed(() => {
  if (!scan.value) return ''
  return `<a href="${reportUrl.value}" target="_blank" rel="noopener">\n  <img src="${badgeUrl.value}" alt="AgentCheck Score: ${scan.value.score}" width="200" />\n</a>`
})

const markdownCode = computed(() => {
  if (!scan.value) return ''
  return `[![AgentCheck Score: ${scan.value.score}](${badgeUrl.value})](${reportUrl.value})`
})

async function fetchData() {
  try {
    scan.value = await getScanResult(scanId)
  } catch (e) {
    error.value = e.message || 'Could not load badge data.'
  } finally {
    loading.value = false
  }
}

onMounted(fetchData)
</script>

<template>
  <div class="flex-1 flex flex-col">
    <!-- Nav -->
    <AppHeader :show-back="'/report/' + scanId" back-label="Report" />

    <!-- Loading -->
    <div v-if="loading" class="flex-1 flex items-center justify-center">
      <svg class="w-6 h-6 text-accent animate-spin" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
      </svg>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="flex-1 flex items-center justify-center px-6">
      <div>
        <p class="text-secondary mb-4 text-sm">{{ error }}</p>
        <router-link to="/" class="btn-primary">Back to home</router-link>
      </div>
    </div>

    <!-- Badge content -->
    <div v-else-if="scan" class="flex-1 px-6 lg:px-8 py-14">
      <div class="max-w-xl mx-auto">

        <!-- Title -->
        <div class="mb-10 animate-fade-in">
          <h1 class="font-display text-2xl font-bold tracking-tight mb-2">Your AgentCheck badge</h1>
          <p class="text-secondary text-sm leading-relaxed prose-body">
            Show visitors and partners that your site has been evaluated for AI agent
            compatibility. Embed the badge on your website, in your README, or in documentation.
          </p>
        </div>

        <!-- Badge Preview -->
        <div class="mb-10 animate-slide-up">
          <p class="section-label mb-3">Preview</p>
          <div class="border border-border rounded-md p-8 bg-warm-50 flex justify-start">
            <div class="inline-flex items-center gap-4 border border-warm-200 rounded-md px-5 py-3 bg-surface">
              <ScoreCircle :score="scan.score" :grade="scan.grade" :size="52" />
              <div>
                <p class="text-sm font-display font-bold text-primary leading-none">AgentCheck</p>
                <p class="text-xs text-muted mt-0.5">{{ scan.domain }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- HTML Embed -->
        <div class="mb-8 animate-slide-up" style="animation-delay: 80ms">
          <p class="section-label mb-2">HTML embed code</p>
          <CodeBlock :code="embedCode" language="html" />
        </div>

        <!-- Markdown -->
        <div class="mb-10 animate-slide-up" style="animation-delay: 160ms">
          <p class="section-label mb-2">Markdown</p>
          <CodeBlock :code="markdownCode" language="markdown" />
        </div>

        <!-- Back link -->
        <div class="animate-slide-up" style="animation-delay: 240ms">
          <router-link
            :to="{ name: 'Report', params: { id: scanId } }"
            class="text-sm text-secondary hover:text-primary transition-colors inline-flex items-center gap-1.5"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
            </svg>
            Back to report
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>
