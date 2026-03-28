<script setup>
import { ref } from 'vue'
import CodeBlock from './CodeBlock.vue'

defineProps({
  fix: { type: Object, required: true },
})

const expanded = ref(false)

const priorityConfig = {
  fail: { label: 'Critical', color: 'text-score-bad', bg: 'bg-score-bad/8', border: 'border-score-bad/20', dot: 'bg-score-bad' },
  warn: { label: 'Warning', color: 'text-score-medium', bg: 'bg-score-medium/8', border: 'border-score-medium/20', dot: 'bg-score-medium' },
  pass: { label: 'OK', color: 'text-score-good', bg: 'bg-score-good/8', border: 'border-score-good/20', dot: 'bg-score-good' },
}
</script>

<template>
  <div class="border-l-2 transition-colors duration-150"
    :class="fix.status === 'fail' ? 'border-score-bad' : 'border-score-medium'"
  >
    <!-- Header row (clickable) -->
    <button
      @click="expanded = !expanded"
      class="w-full text-left pl-5 pr-2 py-3.5 flex items-start gap-3 group focus-visible:outline-none focus-visible:bg-warm-50 rounded-r-md"
    >
      <div class="flex-1 min-w-0">
        <!-- Priority + category -->
        <div class="flex items-center gap-2.5 mb-1">
          <span
            class="inline-flex items-center gap-1.5 text-xs font-display font-semibold"
            :class="priorityConfig[fix.status]?.color || 'text-muted'"
          >
            <span class="w-1.5 h-1.5 rounded-full" :class="priorityConfig[fix.status]?.dot || 'bg-warm-400'" />
            {{ priorityConfig[fix.status]?.label || fix.status }}
          </span>
          <span v-if="fix.category" class="text-xs text-muted">
            {{ fix.category }}
          </span>
        </div>
        <!-- Name -->
        <h3 class="text-sm font-display font-semibold text-primary leading-snug">{{ fix.name }}</h3>
        <!-- Message (always visible) -->
        <p class="text-sm text-secondary mt-1 leading-relaxed prose-body">{{ fix.message }}</p>
      </div>

      <!-- Expand indicator -->
      <span class="flex-shrink-0 mt-1 w-6 h-6 flex items-center justify-center rounded text-warm-400 group-hover:text-secondary transition-colors">
        <svg
          class="w-4 h-4 transition-transform duration-200"
          :class="{ 'rotate-180': expanded }"
          fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"
        >
          <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
        </svg>
      </span>
    </button>

    <!-- Expanded detail -->
    <Transition
      enter-active-class="transition-all duration-250 ease-out"
      enter-from-class="max-h-0 opacity-0"
      enter-to-class="max-h-[800px] opacity-100"
      leave-active-class="transition-all duration-200 ease-in"
      leave-from-class="max-h-[800px] opacity-100"
      leave-to-class="max-h-0 opacity-0"
    >
      <div v-if="expanded" class="overflow-hidden pl-5 pr-2 pb-4">
        <!-- How to fix -->
        <div v-if="fix.fix_suggestion" class="mb-3">
          <p class="section-label mb-1.5">How to fix</p>
          <p class="text-sm text-secondary leading-relaxed prose-body">{{ fix.fix_suggestion }}</p>
        </div>
        <!-- Code snippet -->
        <div v-if="fix.code_snippet">
          <p class="section-label mb-1.5">Code example</p>
          <CodeBlock :code="fix.code_snippet" />
        </div>
      </div>
    </Transition>
  </div>
</template>
