<script setup>
import { computed, ref, onMounted } from 'vue'

const props = defineProps({
  score: { type: Number, default: 0 },
  grade: { type: String, default: '' },
  size: { type: Number, default: 120 },
  showDelta: { type: Number, default: null },
})

const animated = ref(false)
const gradeVisible = ref(false)

const strokeWidth = computed(() => Math.max(4, props.size * 0.04))
const radius = computed(() => (props.size - strokeWidth.value * 2) / 2)
const circumference = computed(() => 2 * Math.PI * radius.value)
const dashOffset = computed(() =>
  circumference.value - (props.score / 100) * circumference.value
)

// Tick mark geometry — 10 marks at each 10% interval
const tickMarks = computed(() => {
  const marks = []
  const cx = props.size / 2
  const cy = props.size / 2
  const outerR = radius.value + strokeWidth.value * 0.8
  const innerR = radius.value + strokeWidth.value * 0.2
  for (let i = 0; i < 10; i++) {
    // Start from top (-90deg), space evenly but skip 0 (start) and end (100%)
    const angle = (i / 10) * 2 * Math.PI - Math.PI / 2
    marks.push({
      x1: cx + innerR * Math.cos(angle),
      y1: cy + innerR * Math.sin(angle),
      x2: cx + outerR * Math.cos(angle),
      y2: cy + outerR * Math.sin(angle),
    })
  }
  return marks
})

const scoreColor = computed(() => {
  if (props.score >= 70) return '#3D8B5E'
  if (props.score >= 40) return '#C08832'
  return '#C25544'
})

const glowColor = computed(() => {
  if (props.score >= 70) return 'rgba(61, 139, 94, 0.22)'
  if (props.score >= 40) return 'rgba(192, 136, 50, 0.22)'
  return 'rgba(194, 85, 68, 0.22)'
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

const deltaLabel = computed(() => {
  if (props.showDelta === null) return ''
  return props.showDelta >= 0 ? `+${props.showDelta}` : `${props.showDelta}`
})

const deltaBg = computed(() => {
  if (props.showDelta === null) return ''
  if (props.showDelta > 0) return 'bg-score-good/10 text-score-good'
  if (props.showDelta < 0) return 'bg-score-bad/10 text-score-bad'
  return 'bg-warm-100 text-muted'
})

onMounted(() => {
  requestAnimationFrame(() => {
    animated.value = true
    // Grade label animates in after the arc (1200ms)
    setTimeout(() => { gradeVisible.value = true }, 1300)
  })
})
</script>

<template>
  <div
    class="relative inline-flex flex-col items-center"
    role="img"
    :aria-label="`Score: ${score} out of 100, grade ${gradeLabel}`"
  >
    <!-- Glow backdrop -->
    <div
      class="absolute rounded-full pointer-events-none transition-opacity duration-700"
      :style="{
        width: size + 'px',
        height: size + 'px',
        background: glowColor,
        filter: `blur(${size * 0.14}px)`,
        opacity: animated ? 1 : 0,
        top: 0,
        left: 0,
      }"
    />

    <div
      class="relative inline-flex items-center justify-center"
      :style="{ width: size + 'px', height: size + 'px' }"
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
          :style="{ filter: `drop-shadow(0 0 ${strokeWidth * 1.2}px ${glowColor})` }"
        />
        <!-- Tick marks (in SVG coordinate space, un-rotated via counter-rotate) -->
        <g :transform="`rotate(90, ${size / 2}, ${size / 2})`">
          <line
            v-for="(tick, i) in tickMarks"
            :key="i"
            :x1="tick.x1"
            :y1="tick.y1"
            :x2="tick.x2"
            :y2="tick.y2"
            :stroke="scoreColor"
            stroke-opacity="0.25"
            :stroke-width="Math.max(1, strokeWidth * 0.35)"
            stroke-linecap="round"
          />
        </g>
      </svg>

      <!-- Center content -->
      <div class="absolute inset-0 flex flex-col items-center justify-center">
        <span
          class="font-display font-bold tabular-nums leading-none"
          :style="{ fontSize: (size * 0.28) + 'px', color: scoreColor }"
        >
          {{ score }}
        </span>
        <span
          class="font-display font-medium text-muted mt-0.5 transition-all duration-300"
          :style="{
            fontSize: Math.max(10, size * 0.11) + 'px',
            opacity: gradeVisible ? 1 : 0,
            transform: gradeVisible ? 'scale(1)' : 'scale(0.7)',
          }"
        >
          {{ gradeLabel }}
        </span>
      </div>
    </div>

    <!-- Delta badge -->
    <div
      v-if="showDelta !== null"
      class="mt-1.5 px-2 py-0.5 rounded-full text-xs font-display font-semibold tabular-nums transition-all duration-500"
      :class="[deltaBg, gradeVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-1']"
      style="transition: opacity 300ms ease, transform 300ms ease;"
    >
      {{ deltaLabel }}
    </div>
  </div>
</template>
