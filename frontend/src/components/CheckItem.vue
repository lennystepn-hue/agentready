<script setup>
defineProps({
  name: { type: String, required: true },
  status: { type: String, default: 'waiting' }, // 'passed', 'failed', 'warning', 'running', 'waiting'
  message: { type: String, default: '' },
})

const statusConfig = {
  passed: { icon: 'check', color: 'text-green-500', bg: 'bg-green-500/10' },
  failed: { icon: 'x', color: 'text-red-500', bg: 'bg-red-500/10' },
  warning: { icon: 'alert', color: 'text-yellow-500', bg: 'bg-yellow-500/10' },
  running: { icon: 'spinner', color: 'text-blue-500', bg: 'bg-blue-500/10' },
  waiting: { icon: 'clock', color: 'text-slate-500', bg: 'bg-slate-500/10' },
}
</script>

<template>
  <div class="flex items-start gap-3 py-2">
    <!-- Status icon -->
    <div
      class="flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center mt-0.5"
      :class="statusConfig[status]?.bg"
    >
      <!-- Check -->
      <svg v-if="status === 'passed'" class="w-3.5 h-3.5 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
        <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
      </svg>
      <!-- X -->
      <svg v-else-if="status === 'failed'" class="w-3.5 h-3.5 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
        <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
      </svg>
      <!-- Warning -->
      <svg v-else-if="status === 'warning'" class="w-3.5 h-3.5 text-yellow-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
        <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01M12 3l9.5 16.5H2.5L12 3z" />
      </svg>
      <!-- Spinner -->
      <svg v-else-if="status === 'running'" class="w-3.5 h-3.5 text-blue-500 animate-spin" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
      </svg>
      <!-- Clock / Waiting -->
      <svg v-else class="w-3.5 h-3.5 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10" />
        <path stroke-linecap="round" d="M12 6v6l4 2" />
      </svg>
    </div>

    <!-- Content -->
    <div class="min-w-0">
      <span class="text-sm font-medium" :class="status === 'waiting' ? 'text-slate-500' : 'text-slate-200'">
        {{ name }}
      </span>
      <p v-if="message" class="text-xs text-slate-500 mt-0.5 truncate">
        {{ message }}
      </p>
    </div>
  </div>
</template>
