<script setup>
import { computed, ref, onMounted } from 'vue'

const props = defineProps({
  name: { type: String, required: true },
  score: { type: Number, required: true },
  maxScore: { type: Number, default: 100 },
})

const animated = ref(false)

const percentage = computed(() =>
  props.maxScore > 0 ? Math.round((props.score / props.maxScore) * 100) : 0
)

const barColor = computed(() => {
  if (percentage.value >= 70) return 'bg-score-good'
  if (percentage.value >= 40) return 'bg-score-medium'
  return 'bg-score-bad'
})

const textColor = computed(() => {
  if (percentage.value >= 70) return 'text-score-good'
  if (percentage.value >= 40) return 'text-score-medium'
  return 'text-score-bad'
})

onMounted(() => {
  requestAnimationFrame(() => {
    animated.value = true
  })
})
</script>

<template>
  <div>
    <div class="flex items-baseline justify-between mb-1.5">
      <span class="text-sm font-display font-medium text-primary">{{ name }}</span>
      <span class="text-sm font-display font-semibold tabular-nums" :class="textColor">
        {{ score }}<span class="text-warm-400 font-normal">/{{ maxScore }}</span>
      </span>
    </div>
    <div class="h-1.5 bg-warm-100 rounded-full overflow-hidden">
      <div
        class="h-full rounded-full transition-all duration-1000 ease-out"
        :class="barColor"
        :style="{ width: animated ? percentage + '%' : '0%' }"
      />
    </div>
  </div>
</template>
