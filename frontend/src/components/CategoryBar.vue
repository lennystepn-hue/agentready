<script setup>
import { computed, ref, onMounted } from 'vue'

const props = defineProps({
  name: { type: String, required: true },
  score: { type: Number, required: true },
  maxScore: { type: Number, default: 100 },
})

const animated = ref(false)
const overshoot = ref(false)
const settled = ref(false)

const percentage = computed(() =>
  props.maxScore > 0 ? Math.round((props.score / props.maxScore) * 100) : 0
)

// Overshoot: briefly fill to min(percentage + 5, 100), then settle to real value
const displayWidth = computed(() => {
  if (!animated.value) return 0
  if (overshoot.value && !settled.value) return Math.min(percentage.value + 5, 100)
  return percentage.value
})

const barColorHex = computed(() => {
  if (percentage.value >= 70) return { fill: '#3D8B5E', dark: '#2d6e49', light: '#5aad7a', shadow: 'rgba(61,139,94,0.35)' }
  if (percentage.value >= 40) return { fill: '#C08832', dark: '#9a6a20', light: '#d9a64d', shadow: 'rgba(192,136,50,0.35)' }
  return { fill: '#C25544', dark: '#9e3e30', light: '#d97060', shadow: 'rgba(194,85,68,0.35)' }
})

const textColor = computed(() => {
  if (percentage.value >= 70) return 'text-score-good'
  if (percentage.value >= 40) return 'text-score-medium'
  return 'text-score-bad'
})

// Threshold markers at 40% and 70%
const thresholds = [40, 70]

onMounted(() => {
  requestAnimationFrame(() => {
    animated.value = true
    overshoot.value = true
    setTimeout(() => {
      settled.value = true
    }, 350)
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

    <!-- Bar track -->
    <div class="relative h-1.5 bg-warm-100 rounded-full overflow-visible">
      <!-- Threshold notch markers (outside overflow:hidden, so we use a separate wrapper) -->
      <div class="absolute inset-0 pointer-events-none z-10">
        <div
          v-for="t in thresholds"
          :key="t"
          class="absolute top-1/2 -translate-y-1/2 w-px h-3 bg-warm-300/80 rounded-full"
          :style="{ left: t + '%' }"
          :title="`${t}% threshold`"
        />
      </div>

      <!-- Filled bar -->
      <div
        class="h-full rounded-full overflow-hidden"
        :style="{
          width: displayWidth + '%',
          transition: settled
            ? 'width 400ms cubic-bezier(0.25, 0.46, 0.45, 0.94)'
            : 'width 320ms cubic-bezier(0.34, 1.3, 0.64, 1)',
        }"
      >
        <!-- Gradient base -->
        <div
          class="h-full w-full relative"
          :style="{
            background: `linear-gradient(to right, ${barColorHex.dark}, ${barColorHex.fill} 60%, ${barColorHex.light})`,
          }"
        >
          <!-- Diagonal stripe texture at 5% opacity -->
          <div
            class="absolute inset-0"
            style="
              background-image: repeating-linear-gradient(
                -45deg,
                transparent,
                transparent 4px,
                rgba(255,255,255,0.08) 4px,
                rgba(255,255,255,0.08) 5px
              );
            "
          />
          <!-- End shadow cap -->
          <div
            class="absolute right-0 top-0 bottom-0 w-3"
            :style="{
              background: `linear-gradient(to right, transparent, ${barColorHex.shadow})`,
            }"
          />
        </div>
      </div>
    </div>
  </div>
</template>
