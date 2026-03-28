<script setup>
import { computed, ref, onMounted } from 'vue'

const props = defineProps({
  name: { type: String, required: true },
  score: { type: Number, required: true },
  maxScore: { type: Number, default: 100 },
})

const animated = ref(false)

const percentage = computed(() =>
  Math.round((props.score / props.maxScore) * 100)
)

const barColor = computed(() => {
  if (percentage.value >= 70) return 'bg-green-500'
  if (percentage.value >= 40) return 'bg-yellow-500'
  return 'bg-red-500'
})

onMounted(() => {
  requestAnimationFrame(() => {
    animated.value = true
  })
})
</script>

<template>
  <div class="space-y-2">
    <div class="flex items-center justify-between">
      <span class="text-sm font-medium text-slate-300">{{ name }}</span>
      <span class="text-sm font-semibold tabular-nums text-slate-400">
        {{ score }}/{{ maxScore }}
      </span>
    </div>
    <div class="h-2 bg-slate-800 rounded-full overflow-hidden">
      <div
        class="h-full rounded-full transition-all duration-1000 ease-out"
        :class="barColor"
        :style="{ width: animated ? percentage + '%' : '0%' }"
      />
    </div>
  </div>
</template>
