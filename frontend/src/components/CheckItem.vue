<script setup>
defineProps({
  name: { type: String, required: true },
  status: { type: String, default: 'waiting' },
  message: { type: String, default: '' },
})
</script>

<template>
  <div class="flex items-start gap-3 py-2.5 border-b border-border-light last:border-b-0">
    <!-- Status indicator -->
    <div class="flex-shrink-0 mt-0.5">
      <!-- Pass -->
      <svg v-if="status === 'pass' || status === 'passed'" class="w-[18px] h-[18px]" viewBox="0 0 18 18" fill="none">
        <circle cx="9" cy="9" r="9" fill="#3D8B5E" />
        <path d="M6 9.5l2 2 4-4" stroke="#fff" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
      </svg>
      <!-- Fail -->
      <svg v-else-if="status === 'fail' || status === 'failed'" class="w-[18px] h-[18px]" viewBox="0 0 18 18" fill="none">
        <circle cx="9" cy="9" r="9" fill="#C25544" />
        <path d="M6.5 6.5l5 5M11.5 6.5l-5 5" stroke="#fff" stroke-width="1.5" stroke-linecap="round" />
      </svg>
      <!-- Warn -->
      <svg v-else-if="status === 'warn' || status === 'warning'" class="w-[18px] h-[18px]" viewBox="0 0 18 18" fill="none">
        <circle cx="9" cy="9" r="9" fill="#C08832" />
        <path d="M9 6v3.5" stroke="#fff" stroke-width="1.5" stroke-linecap="round" />
        <circle cx="9" cy="12" r="0.75" fill="#fff" />
      </svg>
      <!-- Running -->
      <svg v-else-if="status === 'running'" class="w-[18px] h-[18px] animate-spin text-accent" fill="none" viewBox="0 0 18 18">
        <circle cx="9" cy="9" r="7" stroke="currentColor" stroke-width="1.5" opacity="0.2" />
        <path d="M9 2a7 7 0 014.95 2.05" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" />
      </svg>
      <!-- Waiting -->
      <svg v-else class="w-[18px] h-[18px] text-warm-300" viewBox="0 0 18 18" fill="none">
        <circle cx="9" cy="9" r="7" stroke="currentColor" stroke-width="1" stroke-dasharray="3 3" />
      </svg>
    </div>

    <!-- Content -->
    <div class="min-w-0 flex-1">
      <span
        class="text-sm"
        :class="status === 'waiting' ? 'text-muted' : 'text-primary'"
      >
        {{ name }}
      </span>
      <p v-if="message && status !== 'waiting'" class="text-xs text-secondary mt-0.5 leading-relaxed">
        {{ message }}
      </p>
    </div>
  </div>
</template>
