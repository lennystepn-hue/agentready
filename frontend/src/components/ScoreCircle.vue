<script setup>
import { computed, ref, onMounted } from 'vue'

const props = defineProps({
  score: { type: Number, default: 0 },
  grade: { type: String, default: '' },
  size: { type: Number, default: 200 },
})

const animated = ref(false)

const radius = computed(() => (props.size - 16) / 2)
const circumference = computed(() => 2 * Math.PI * radius.value)
const dashOffset = computed(() =>
  circumference.value - (props.score / 100) * circumference.value
)

const scoreColor = computed(() => {
  if (props.score >= 70) return '#22c55e'
  if (props.score >= 40) return '#eab308'
  return '#ef4444'
})

const scoreColorClass = computed(() => {
  if (props.score >= 70) return 'text-green-500'
  if (props.score >= 40) return 'text-yellow-500'
  return 'text-red-500'
})

const gradeLabel = computed(() => {
  if (props.grade) return props.grade
  if (props.score >= 90) return 'A+'
  if (props.score >= 80) return 'A'
  if (props.score >= 70) return 'B'
  if (props.score >= 60) return 'C'
  if (props.score >= 40) return 'D'
  return 'F'
})

onMounted(() => {
  requestAnimationFrame(() => {
    animated.value = true
  })
})
</script>

<template>
  <div class="relative inline-flex items-center justify-center" :style="{ width: size + 'px', height: size + 'px' }">
    <svg
      :width="size"
      :height="size"
      class="-rotate-90"
    >
      <!-- Background ring -->
      <circle
        :cx="size / 2"
        :cy="size / 2"
        :r="radius"
        fill="none"
        stroke="#1e293b"
        stroke-width="8"
      />
      <!-- Score ring -->
      <circle
        :cx="size / 2"
        :cy="size / 2"
        :r="radius"
        fill="none"
        :stroke="scoreColor"
        stroke-width="8"
        stroke-linecap="round"
        :stroke-dasharray="circumference"
        :stroke-dashoffset="animated ? dashOffset : circumference"
        class="transition-all duration-[1500ms] ease-out"
      />
    </svg>
    <!-- Center text -->
    <div class="absolute inset-0 flex flex-col items-center justify-center">
      <span
        class="font-bold tabular-nums"
        :class="scoreColorClass"
        :style="{ fontSize: (size * 0.22) + 'px' }"
      >
        {{ score }}
      </span>
      <span
        class="font-semibold text-slate-400 uppercase tracking-wider"
        :style="{ fontSize: (size * 0.09) + 'px' }"
      >
        {{ gradeLabel }}
      </span>
    </div>
  </div>
</template>
