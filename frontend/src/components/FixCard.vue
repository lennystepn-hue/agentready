<script setup>
import { ref } from 'vue'
import CodeBlock from './CodeBlock.vue'

defineProps({
  fix: {
    type: Object,
    required: true,
    // Expected shape: { name, category, status, message, fix_suggestion, code_snippet }
  },
})

const expanded = ref(false)

const priorityConfig = {
  high: { label: 'Hoch', class: 'bg-red-500/10 text-red-400 border-red-500/20' },
  medium: { label: 'Mittel', class: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20' },
  low: { label: 'Niedrig', class: 'bg-blue-500/10 text-blue-400 border-blue-500/20' },
}
</script>

<template>
  <div class="card transition-all duration-200 hover:border-slate-700">
    <!-- Header -->
    <button
      @click="expanded = !expanded"
      class="w-full flex items-start justify-between gap-4 text-left"
    >
      <div class="flex-1 min-w-0">
        <div class="flex items-center gap-2 flex-wrap">
          <span
            v-if="fix.status"
            class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border"
            :class="priorityConfig[fix.status]?.class || 'bg-slate-500/10 text-slate-400 border-slate-500/20'"
          >
            {{ priorityConfig[fix.status]?.label || fix.status }}
          </span>
          <span
            v-if="fix.category"
            class="text-xs text-slate-500 font-medium"
          >
            {{ fix.category }}
          </span>
        </div>
        <h3 class="text-sm font-semibold text-slate-200 mt-1.5">{{ fix.name }}</h3>
        <p class="text-sm text-slate-400 mt-1">{{ fix.message }}</p>
      </div>
      <!-- Expand chevron -->
      <svg
        class="w-5 h-5 text-slate-500 flex-shrink-0 transition-transform duration-200 mt-1"
        :class="{ 'rotate-180': expanded }"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        stroke-width="2"
      >
        <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
      </svg>
    </button>

    <!-- Expandable content -->
    <Transition
      enter-active-class="transition-all duration-300 ease-out"
      enter-from-class="max-h-0 opacity-0"
      enter-to-class="max-h-[600px] opacity-100"
      leave-active-class="transition-all duration-200 ease-in"
      leave-from-class="max-h-[600px] opacity-100"
      leave-to-class="max-h-0 opacity-0"
    >
      <div v-if="expanded" class="overflow-hidden">
        <!-- Fix suggestion -->
        <div v-if="fix.fix_suggestion" class="mt-4 p-3 bg-blue-500/5 border border-blue-500/10 rounded-lg">
          <p class="text-sm text-blue-300 flex items-start gap-2">
            <svg class="w-4 h-4 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            {{ fix.fix_suggestion }}
          </p>
        </div>
        <!-- Code snippet -->
        <div v-if="fix.code_snippet" class="mt-4">
          <CodeBlock :code="fix.code_snippet" />
        </div>
      </div>
    </Transition>
  </div>
</template>
