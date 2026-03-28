<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { initAuth, isLoggedIn, user } from '../auth.js'

const route = useRoute()

const type = computed(() => route.query.type || 'pro')
const scanId = computed(() => route.query.scan_id || '')

onMounted(async () => {
  // Refresh user data to pick up new plan or purchase
  await initAuth()
})
</script>

<template>
  <div class="flex-1 flex flex-col">
    <!-- Nav -->
    <nav class="border-b border-border-light">
      <div class="max-w-5xl mx-auto px-6 lg:px-8 h-14 flex items-center justify-between">
        <router-link to="/" class="flex items-center gap-2">
          <svg class="w-5 h-5 text-accent" viewBox="0 0 24 24" fill="none">
            <path d="M12 2L4 20h4l1.5-4h5L16 20h4L12 2zm0 7l2 5h-4l2-5z" fill="currentColor"/>
            <path d="M20 8a10 10 0 00-4-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" opacity="0.5"/>
            <path d="M22 6a14 14 0 00-6-5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" opacity="0.3"/>
          </svg>
          <span class="font-display font-bold text-[15px] tracking-tight">AgentCheck</span>
        </router-link>
        <div class="flex items-center gap-4">
          <router-link v-if="isLoggedIn" to="/dashboard" class="text-[13px] text-secondary hover:text-primary transition-colors">Dashboard</router-link>
          <router-link v-else to="/login" class="text-[13px] text-secondary hover:text-primary transition-colors">Sign in</router-link>
        </div>
      </div>
    </nav>

    <!-- Content -->
    <div class="flex-1 flex items-start justify-center px-6 lg:px-8 py-16 sm:py-24">
      <div class="w-full max-w-md text-center animate-fade-in">
        <!-- Success icon -->
        <div class="w-16 h-16 rounded-full bg-score-good/10 flex items-center justify-center mx-auto mb-6">
          <svg class="w-8 h-8 text-score-good" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
          </svg>
        </div>

        <h1 class="font-display text-2xl font-bold tracking-tight text-primary mb-3">Payment successful!</h1>

        <p v-if="type === 'fix_files'" class="text-secondary leading-relaxed mb-8">
          Your fix files are ready. Head to your report to download them.
        </p>
        <p v-else class="text-secondary leading-relaxed mb-8">
          Your Pro plan is now active. You have full access to monitoring, competitor comparison, score history, and unlimited fix files.
        </p>

        <div class="flex flex-col sm:flex-row gap-3 justify-center">
          <router-link
            v-if="type === 'fix_files' && scanId"
            :to="{ name: 'Report', params: { id: scanId } }"
            class="btn-primary"
          >
            Go to report
          </router-link>
          <router-link to="/dashboard" class="btn-secondary">
            Go to dashboard
          </router-link>
        </div>
      </div>
    </div>

    <!-- Footer -->
    <footer class="border-t border-border-light py-6 px-6 lg:px-8 mt-auto">
      <div class="max-w-5xl mx-auto flex items-center justify-between">
        <span class="text-xs text-muted">&copy; {{ new Date().getFullYear() }} AgentCheck</span>
        <a
          href="https://github.com/lennystepn-hue/agentready"
          target="_blank"
          rel="noopener"
          class="text-xs text-secondary hover:text-primary transition-colors"
        >
          GitHub
        </a>
      </div>
    </footer>
  </div>
</template>
