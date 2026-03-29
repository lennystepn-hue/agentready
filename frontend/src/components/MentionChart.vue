<script setup>
import { computed } from 'vue'
const props = defineProps({ data: { type: Array, default: () => [] } })
const bars = computed(() => {
  return props.data.slice().reverse().map(d => ({
    week: d.week_date || d.week,
    pct: d.queries_tested > 0 ? Math.round((d.queries_found / d.queries_tested) * 100) : 0,
    found: d.queries_found, tested: d.queries_tested,
  }))
})
</script>
<template>
  <div class="flex items-end gap-1 h-12">
    <div v-for="(bar, idx) in bars" :key="idx"
      class="flex-1 min-w-[6px] rounded-t transition-all"
      :class="bar.pct > 50 ? 'bg-score-good' : bar.pct > 0 ? 'bg-score-medium' : 'bg-warm-200'"
      :style="{ height: Math.max(bar.pct, 8) + '%' }"
      :title="`${bar.week}: ${bar.found}/${bar.tested}`"
    />
  </div>
</template>
