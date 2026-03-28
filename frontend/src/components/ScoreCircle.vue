<script setup>
import { computed, ref, onMounted } from 'vue'

const props = defineProps({
  score: { type: Number, default: 0 },
  grade: { type: String, default: '' },
  size: { type: Number, default: 120 },
})

const animated = ref(false)

const strokeWidth = computed(() => Math.max(4, props.size * 0.04))
const radius = computed(() => (props.size - strokeWidth.value * 2) / 2)
const circumference = computed(() => 2 * Math.PI * radius.value)
const dashOffset = computed(() =>
  circumference.value - (props.score / 100) * circumference.value
)

const scoreColor = computed(() => {
  if (props.score >= 70) return '#3D8B5E'
  if (props.score >= 40) return '#C08832'
  return '#C25544'
})

const trackColor = computed(() => {
  if (props.score >= 70) return '#3D8B5E18'
  if (props.score >= 40) return '#C0883218'
  return '#C2554418'
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
  <div
    class="relative inline-flex items-center justify-center"
    :style="{ width: size + 'px', height: size + 'px' }"
    role="img"
    :aria-label="`Score: ${score} out of 100, grade ${gradeLabel}`"
  >
    <svg :width="size" :height="size" class="-rotate-90">
      <!-- Track -->
      <circle
        :cx="size / 2"
        :cy="size / 2"
        :r="radius"
        fill="none"
        :stroke="trackColor"
        :stroke-width="strokeWidth"
      />
      <!-- Value arc -->
      <circle
        :cx="size / 2"
        :cy="size / 2"
        :r="radius"
        fill="none"
        :stroke="scoreColor"
        :stroke-width="strokeWidth"
        stroke-linecap="round"
        :stroke-dasharray="circumference"
        :stroke-dashoffset="animated ? dashOffset : circumference"
        class="transition-all duration-[1200ms] ease-out"
      />
    </svg>
    <div class="absolute inset-0 flex flex-col items-center justify-center">
      <span
        class="font-display font-bold tabular-nums leading-none"
        :style="{ fontSize: (size * 0.28) + 'px', color: scoreColor }"
      >
        {{ score }}
      </span>
      <span
        class="font-display font-medium text-muted mt-0.5"
        :style="{ fontSize: Math.max(10, size * 0.11) + 'px' }"
      >
        {{ gradeLabel }}
      </span>
    </div>
  </div>
</template>
