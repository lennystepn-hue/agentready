<script setup>
import { computed, ref, onMounted } from 'vue'

const props = defineProps({ data: { type: Array, default: () => [] } })

const mounted = ref(false)

const bars = computed(() => {
  return props.data.slice().reverse().map(d => {
    const pct = d.queries_tested > 0
      ? Math.round((d.queries_found / d.queries_tested) * 100)
      : 0
    // Abbreviated date label: "Mar 3" style
    const raw = d.week_date || d.week || ''
    let label = raw
    try {
      const dt = new Date(raw)
      if (!isNaN(dt)) {
        label = dt.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
      }
    } catch {}
    return {
      week: raw,
      label,
      pct,
      found: d.queries_found ?? 0,
      tested: d.queries_tested ?? 0,
    }
  })
})

onMounted(() => {
  requestAnimationFrame(() => {
    setTimeout(() => { mounted.value = true }, 30)
  })
})
</script>

<template>
  <div class="flex gap-3">
    <!-- Y axis labels -->
    <div class="flex flex-col justify-between items-end pb-5 text-[10px] font-display text-muted select-none flex-shrink-0" style="min-width: 28px;">
      <span>100%</span>
      <span>0%</span>
    </div>

    <!-- Chart area -->
    <div class="flex-1 min-w-0">
      <!-- Bar area with baseline -->
      <div class="relative h-16">
        <!-- 50% baseline -->
        <div
          class="absolute left-0 right-0 border-t border-dashed border-warm-300/60 pointer-events-none z-10"
          style="top: 50%;"
          aria-hidden="true"
        />

        <!-- Bars row -->
        <div class="flex items-end gap-1 h-full">
          <div
            v-for="(bar, idx) in bars"
            :key="idx"
            class="group relative flex-1 min-w-[6px] rounded-t cursor-default"
            :style="{
              height: mounted ? Math.max(bar.pct, 8) + '%' : '8%',
              transition: `height 600ms cubic-bezier(0.34, 1.2, 0.64, 1) ${idx * 40}ms`,
              background: bar.pct > 50
                ? 'linear-gradient(to top, #2d6e49, #3D8B5E, #5aad7a)'
                : bar.pct > 0
                  ? 'linear-gradient(to top, #9a6a20, #C08832, #d9a64d)'
                  : 'linear-gradient(to top, #D4D0C8, #E8E5E0)',
              boxShadow: bar.pct > 50
                ? '0 -1px 4px rgba(61,139,94,0.25)'
                : bar.pct > 0
                  ? '0 -1px 4px rgba(192,136,50,0.25)'
                  : 'none',
            }"
          >
            <!-- CSS-only tooltip -->
            <div
              class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 z-20
                     bg-primary text-page text-[11px] font-display whitespace-nowrap
                     rounded px-2 py-1 leading-tight pointer-events-none
                     opacity-0 group-hover:opacity-100 transition-opacity duration-150
                     shadow-lg"
              role="tooltip"
            >
              <div class="font-semibold">{{ bar.label || bar.week }}</div>
              <div class="text-warm-400 mt-0.5">{{ bar.found }}/{{ bar.tested }} found</div>
              <!-- Arrow -->
              <div class="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-primary" />
            </div>
          </div>
        </div>
      </div>

      <!-- X axis: week date labels -->
      <div class="flex items-start gap-1 mt-1">
        <div
          v-for="(bar, idx) in bars"
          :key="idx"
          class="flex-1 min-w-0 text-center text-[9px] font-display text-muted truncate select-none"
          :title="bar.week"
        >
          {{ bar.label }}
        </div>
      </div>
    </div>
  </div>
</template>
