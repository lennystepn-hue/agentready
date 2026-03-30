<script setup>
import { computed, ref, onMounted } from 'vue'

const props = defineProps({ steps: { type: Array, default: () => [] } })

const mounted = ref(false)

const passCount = computed(() => props.steps.filter(s => s.status === 'pass').length)
const completionPct = computed(() =>
  props.steps.length > 0 ? Math.round((passCount.value / props.steps.length) * 100) : 0
)

onMounted(() => {
  requestAnimationFrame(() => {
    setTimeout(() => { mounted.value = true }, 30)
  })
})
</script>

<template>
  <div>
    <!-- Completion bar -->
    <div class="mb-4">
      <div class="flex items-baseline justify-between mb-1">
        <span class="text-xs font-display font-medium text-muted">Completion</span>
        <span class="text-xs font-display font-semibold tabular-nums text-primary">{{ completionPct }}%</span>
      </div>
      <div class="h-1 bg-warm-100 rounded-full overflow-hidden">
        <div
          class="h-full rounded-full bg-score-good transition-all duration-700 ease-out"
          :style="{ width: mounted ? completionPct + '%' : '0%' }"
        />
      </div>
    </div>

    <!-- Steps list -->
    <div class="relative">
      <!-- Vertical connector line -->
      <div
        v-if="steps.length > 1"
        class="absolute left-[11px] top-4 bottom-4 w-px bg-warm-200 pointer-events-none"
        aria-hidden="true"
      />

      <div class="space-y-2">
        <div
          v-for="(step, idx) in steps"
          :key="idx"
          class="group relative flex items-start gap-3 transition-all duration-300"
          :style="{
            opacity: mounted ? 1 : 0,
            transform: mounted ? 'translateX(0)' : 'translateX(-8px)',
            transitionDelay: `${idx * 60}ms`,
          }"
        >
          <!-- Dot / icon -->
          <div class="relative z-10 mt-0.5 flex-shrink-0">
            <!-- Pass: check animates in -->
            <div
              v-if="step.status === 'pass'"
              class="w-6 h-6 rounded-full bg-score-good flex items-center justify-center
                     shadow-sm shadow-score-good/20"
            >
              <svg
                class="w-3.5 h-3.5 text-white transition-all duration-300"
                :style="{
                  strokeDasharray: 20,
                  strokeDashoffset: mounted ? 0 : 20,
                  transitionDelay: `${idx * 60 + 300}ms`,
                }"
                fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3"
              >
                <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
              </svg>
            </div>

            <!-- Fail: pulsing red dot -->
            <div
              v-else-if="step.status === 'fail'"
              class="w-6 h-6 rounded-full bg-score-bad flex items-center justify-center relative"
            >
              <!-- Pulse ring -->
              <span class="absolute inset-0 rounded-full bg-score-bad animate-ping opacity-30" />
              <svg class="w-3.5 h-3.5 text-white relative z-10" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>

            <!-- Blocked: numbered dot -->
            <div
              v-else
              class="w-6 h-6 rounded-full bg-warm-200 flex items-center justify-center"
            >
              <span class="text-xs font-display font-bold text-warm-500">{{ idx + 1 }}</span>
            </div>
          </div>

          <!-- Text content -->
          <div class="flex-1 min-w-0 pb-0.5">
            <p
              class="text-sm leading-snug"
              :class="step.status === 'blocked' ? 'text-muted' : 'text-primary'"
            >
              {{ step.name }}
            </p>
            <!-- Detail: always rendered for hover; fail detail always visible -->
            <p
              v-if="step.status === 'fail' && step.detail"
              class="text-xs text-score-bad mt-0.5"
            >
              {{ step.detail }}
            </p>
            <p
              v-else-if="step.detail"
              class="text-xs text-muted mt-0.5 overflow-hidden max-h-0 group-hover:max-h-10
                     transition-all duration-200 ease-out opacity-0 group-hover:opacity-100"
            >
              {{ step.detail }}
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
