<script setup>
defineProps({ steps: { type: Array, default: () => [] } })
</script>
<template>
  <div class="space-y-2">
    <div v-for="(step, idx) in steps" :key="idx" class="flex items-center gap-3">
      <div class="w-6 h-6 rounded-full flex items-center justify-center text-xs font-display font-bold flex-shrink-0"
        :class="{
          'bg-score-good text-white': step.status === 'pass',
          'bg-score-bad text-white': step.status === 'fail',
          'bg-warm-200 text-warm-500': step.status === 'blocked',
        }">
        <svg v-if="step.status === 'pass'" class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" /></svg>
        <svg v-else-if="step.status === 'fail'" class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>
        <span v-else>{{ idx + 1 }}</span>
      </div>
      <div class="flex-1 min-w-0">
        <p class="text-sm" :class="step.status === 'blocked' ? 'text-muted' : 'text-primary'">{{ step.name }}</p>
        <p v-if="step.status === 'fail'" class="text-xs text-score-bad">{{ step.detail }}</p>
      </div>
    </div>
  </div>
</template>
