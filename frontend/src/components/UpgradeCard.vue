<script setup>
import { ref } from 'vue'
import { createCheckoutSession } from '../api.js'

defineProps({
  compact: {
    type: Boolean,
    default: false,
  },
})

const loading = ref(false)
const error = ref('')

async function handleUpgrade() {
  loading.value = true
  error.value = ''
  try {
    const { url } = await createCheckoutSession('pro', null)
    window.location.href = url
  } catch (e) {
    error.value = e.message || 'Something went wrong. Please try again.'
  } finally {
    loading.value = false
  }
}

const features = [
  'Unlimited tailored fix files',
  'Weekly monitoring + score alerts',
  'AI Discovery Test — see if ChatGPT/Claude find you',
  'AI-powered competitor analysis',
  'Score history over time',
]
</script>

<template>
  <!-- Compact variant -->
  <div
    v-if="compact"
    class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border border-accent/20 rounded-lg bg-accent/[0.03] px-5 py-4"
  >
    <div class="min-w-0">
      <p class="font-display font-semibold text-warm-900 text-sm">Get found by AI agents</p>
      <p class="text-sm text-warm-500 mt-0.5">
        Pro unlocks monitoring, discovery tests, and competitor insights.
      </p>
    </div>
    <button
      @click="handleUpgrade"
      :disabled="loading"
      class="btn-primary text-sm px-4 py-2 shrink-0 disabled:opacity-60"
    >
      <template v-if="loading">Processing...</template>
      <template v-else>Upgrade — $29/mo</template>
    </button>
    <p v-if="error" class="text-sm text-red-600 w-full">{{ error }}</p>
  </div>

  <!-- Full variant -->
  <div
    v-else
    class="border border-accent/20 rounded-lg overflow-hidden"
  >
    <div class="bg-accent/[0.04] px-6 py-8 sm:px-8">
      <p class="text-xs font-semibold uppercase tracking-wider text-accent font-display">Pro Plan</p>
      <h3 class="mt-3 text-xl sm:text-2xl font-display font-bold text-warm-900">
        Make AI agents recommend your site
      </h3>
      <p class="mt-2 text-warm-600 text-sm leading-relaxed max-w-xl">
        We don't just tell you what's wrong — we help you fix it, monitor your progress, and verify that AI agents actually find you.
      </p>

      <ul class="mt-6 space-y-3">
        <li
          v-for="feature in features"
          :key="feature"
          class="flex items-start gap-3"
        >
          <svg class="w-5 h-5 text-accent shrink-0 mt-0.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="20 6 9 17 4 12" />
          </svg>
          <span class="text-sm text-warm-700">{{ feature }}</span>
        </li>
      </ul>

      <div class="mt-8 flex flex-col sm:flex-row items-start sm:items-center gap-3">
        <button
          @click="handleUpgrade"
          :disabled="loading"
          class="btn-primary px-6 py-2.5 text-sm disabled:opacity-60"
        >
          <template v-if="loading">Processing...</template>
          <template v-else>Start Pro — $29/mo</template>
        </button>
        <span class="text-xs text-warm-400">Cancel anytime</span>
      </div>

      <p v-if="error" class="mt-3 text-sm text-red-600">{{ error }}</p>
    </div>
  </div>
</template>
