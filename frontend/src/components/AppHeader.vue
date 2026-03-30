<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { isLoggedIn } from '../auth.js'
import UserDropdown from './UserDropdown.vue'

defineProps({
  showBack: { type: String, default: '' },
  backLabel: { type: String, default: 'Back' },
  fullWidth: { type: Boolean, default: false },
})

const scrollY = ref(0)
const scrollProgress = ref(0)
const isScrolled = ref(false)

function onScroll() {
  scrollY.value = window.scrollY
  isScrolled.value = window.scrollY > 4

  const docHeight = document.documentElement.scrollHeight - window.innerHeight
  scrollProgress.value = docHeight > 0
    ? Math.min(100, (window.scrollY / docHeight) * 100)
    : 0
}

onMounted(() => window.addEventListener('scroll', onScroll, { passive: true }))
onUnmounted(() => window.removeEventListener('scroll', onScroll))
</script>

<template>
  <header
    class="sticky top-0 z-50 border-b transition-all duration-200"
    :class="[
      isScrolled ? 'border-border-light shadow-sm' : 'border-transparent',
    ]"
    :style="{
      backgroundColor: isScrolled ? 'rgba(250,250,248,0.90)' : 'rgba(250,250,248,0.95)',
      backdropFilter: 'blur(8px)',
    }"
  >
    <!-- Scroll progress line -->
    <div
      class="absolute top-0 left-0 h-[1.5px] bg-accent transition-none pointer-events-none z-10"
      :style="{ width: scrollProgress + '%', opacity: scrollProgress > 0 ? 1 : 0 }"
      aria-hidden="true"
    />

    <div
      class="h-14 flex items-center justify-between"
      :class="fullWidth ? 'px-5' : 'max-w-5xl mx-auto px-6 lg:px-8'"
    >
      <!-- Left: Logo + back -->
      <div class="flex items-center gap-3">
        <router-link to="/" class="flex items-center gap-2 flex-shrink-0">
          <svg class="w-5 h-5 text-accent" viewBox="0 0 24 24" fill="none">
            <path d="M12 2L4 20h4l1.5-4h5L16 20h4L12 2zm0 7l2 5h-4l2-5z" fill="currentColor"/>
            <path d="M20 8a10 10 0 00-4-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" opacity="0.5"/>
            <path d="M22 6a14 14 0 00-6-5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" opacity="0.3"/>
          </svg>
          <span class="font-display font-bold text-[15px] tracking-tight text-primary">AgentCheck</span>
        </router-link>

        <!-- Back button -->
        <router-link
          v-if="showBack"
          :to="showBack"
          class="hidden sm:flex items-center gap-1 text-[13px] text-secondary hover:text-primary transition-colors"
        >
          <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
          </svg>
          {{ backLabel }}
        </router-link>

        <!-- Center nav links (from slot) — only on wider screens -->
        <div class="hidden md:flex items-center gap-5 ml-6">
          <slot name="actions" />
        </div>
      </div>

      <!-- Right: compact group -->
      <div class="flex items-center gap-4">
        <router-link to="/pricing" class="hidden sm:block text-[13px] text-secondary hover:text-primary transition-colors">
          Pricing
        </router-link>

        <a
          href="https://github.com/lennystepn-hue/agentcheck"
          target="_blank"
          rel="noopener"
          class="hidden sm:block text-warm-400 hover:text-secondary transition-colors"
          aria-label="GitHub"
        >
          <svg class="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z" />
          </svg>
        </a>

        <!-- Auth -->
        <UserDropdown v-if="isLoggedIn" />
        <router-link v-else to="/login" class="text-[13px] font-display font-medium text-accent hover:text-accent-hover transition-colors">
          Sign in
        </router-link>
      </div>
    </div>
  </header>
</template>
