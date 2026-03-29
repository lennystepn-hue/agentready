<script setup>
import { isLoggedIn } from '../auth.js'
import UserDropdown from './UserDropdown.vue'
import { useRoute } from 'vue-router'

const route = useRoute()

defineProps({
  showBack: {
    type: String,
    default: '',
  },
  backLabel: {
    type: String,
    default: 'Back',
  },
})
</script>

<template>
  <header class="sticky top-0 z-50 bg-page/95 backdrop-blur-sm border-b border-border-light">
    <div class="h-14 max-w-7xl mx-auto px-4 sm:px-6 flex items-center justify-between gap-4">
      <!-- Left -->
      <div class="flex items-center gap-3 min-w-0">
        <router-link to="/" class="flex items-center gap-2 shrink-0">
          <svg class="w-5 h-5 text-accent" viewBox="0 0 24 24" fill="none">
            <path d="M12 2L4 20h4l1.5-4h5L16 20h4L12 2zm0 7l2 5h-4l2-5z" fill="currentColor"/>
            <path d="M20 8a10 10 0 00-4-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" opacity="0.5"/>
            <path d="M22 6a14 14 0 00-6-5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" opacity="0.3"/>
          </svg>
          <span class="font-display font-semibold text-warm-900 text-sm">AgentCheck</span>
        </router-link>

        <router-link
          v-if="showBack"
          :to="showBack"
          class="hidden sm:flex items-center gap-1 text-sm text-warm-500 hover:text-warm-700 transition-colors ml-2"
        >
          <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="15 18 9 12 15 6" />
          </svg>
          {{ backLabel }}
        </router-link>
      </div>

      <!-- Right -->
      <div class="flex items-center gap-4">
        <slot name="actions" />

        <router-link
          to="/pricing"
          class="text-sm font-medium transition-colors"
          :class="route.path === '/pricing' ? 'text-accent' : 'text-warm-600 hover:text-warm-800'"
        >
          Pricing
        </router-link>

        <a
          href="https://github.com"
          target="_blank"
          rel="noopener noreferrer"
          class="text-warm-400 hover:text-warm-600 transition-colors"
          aria-label="GitHub"
        >
          <svg class="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z" />
          </svg>
        </a>

        <template v-if="isLoggedIn">
          <UserDropdown />
        </template>
        <template v-else>
          <router-link
            to="/login"
            class="text-sm font-medium text-accent hover:text-accent/80 transition-colors"
          >
            Sign in
          </router-link>
        </template>
      </div>
    </div>
  </header>
</template>
