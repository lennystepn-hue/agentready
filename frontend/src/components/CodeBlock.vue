<script setup>
import { ref } from 'vue'

defineProps({
  code: { type: String, required: true },
  language: { type: String, default: 'html' },
})

const copied = ref(false)

function copyCode(code) {
  navigator.clipboard.writeText(code).then(() => {
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
  })
}
</script>

<template>
  <div class="relative group rounded-lg overflow-hidden border border-slate-800 bg-slate-950">
    <!-- Language label -->
    <div class="flex items-center justify-between px-4 py-2 bg-slate-900/50 border-b border-slate-800">
      <span class="text-xs font-medium text-slate-500 uppercase tracking-wider">{{ language }}</span>
      <button
        @click="copyCode(code)"
        class="text-xs text-slate-500 hover:text-slate-300 transition-colors flex items-center gap-1"
      >
        <svg v-if="!copied" class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
          <path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1" />
        </svg>
        <svg v-else class="w-3.5 h-3.5 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
        </svg>
        {{ copied ? 'Kopiert!' : 'Kopieren' }}
      </button>
    </div>
    <!-- Code content -->
    <pre class="p-4 overflow-x-auto text-sm leading-relaxed"><code class="text-slate-300">{{ code }}</code></pre>
  </div>
</template>
