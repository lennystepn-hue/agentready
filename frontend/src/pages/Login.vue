<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { isLoggedIn } from '../auth.js'
import { login, register } from '../auth.js'

const router = useRouter()
const route = useRoute()

const mode = ref('login')
const email = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

function switchMode(m) {
  mode.value = m
  error.value = ''
}

async function handleSubmit() {
  error.value = ''
  loading.value = true
  try {
    if (mode.value === 'login') {
      await login(email.value, password.value)
    } else {
      await register(email.value, password.value)
    }
    const redirect = route.query.redirect || '/dashboard'
    router.push(redirect)
  } catch (e) {
    error.value = e.message || 'Something went wrong. Please try again.'
  } finally {
    loading.value = false
  }
}

// Redirect if already logged in
if (isLoggedIn.value) {
  router.replace(route.query.redirect || '/dashboard')
}
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
        <div class="flex items-center gap-6">
          <router-link to="/" class="text-[13px] text-secondary hover:text-primary transition-colors inline-flex items-center gap-1">
            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
            </svg>
            Back to home
          </router-link>
          <router-link to="/pricing" class="text-[13px] text-secondary hover:text-primary transition-colors">Pricing</router-link>
        </div>
      </div>
    </nav>

    <!-- Content -->
    <div class="flex-1 flex items-start justify-center px-6 lg:px-8 py-16 sm:py-24">
      <div class="w-full max-w-sm animate-fade-in">
        <!-- Tab toggle -->
        <div class="flex gap-1 mb-8 bg-warm-100 rounded-md p-1">
          <button
            @click="switchMode('login')"
            class="flex-1 py-2 text-sm font-display font-semibold rounded transition-colors"
            :class="mode === 'login' ? 'bg-surface text-primary shadow-sm' : 'text-secondary hover:text-primary'"
          >
            Sign in
          </button>
          <button
            @click="switchMode('register')"
            class="flex-1 py-2 text-sm font-display font-semibold rounded transition-colors"
            :class="mode === 'register' ? 'bg-surface text-primary shadow-sm' : 'text-secondary hover:text-primary'"
          >
            Create account
          </button>
        </div>

        <!-- Form -->
        <form @submit.prevent="handleSubmit" class="space-y-4">
          <div>
            <label for="email" class="block text-sm font-display font-medium text-primary mb-1.5">Email</label>
            <input
              id="email"
              v-model="email"
              type="email"
              required
              autocomplete="email"
              placeholder="you@example.com"
              class="input-field"
              :disabled="loading"
            />
          </div>
          <div>
            <label for="password" class="block text-sm font-display font-medium text-primary mb-1.5">Password</label>
            <input
              id="password"
              v-model="password"
              type="password"
              required
              autocomplete="current-password"
              placeholder="Your password"
              class="input-field"
              :disabled="loading"
            />
          </div>

          <p v-if="error" class="text-sm text-score-bad">{{ error }}</p>

          <button
            type="submit"
            class="btn-primary w-full"
            :disabled="loading || !email.trim() || !password.trim()"
          >
            <svg v-if="loading" class="w-4 h-4 mr-2 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            {{ loading ? 'Please wait...' : (mode === 'login' ? 'Sign in' : 'Create account') }}
          </button>
        </form>

        <p class="mt-6 text-xs text-muted text-center leading-relaxed">
          Free forever. Create an account to unlock paid features.
        </p>
      </div>
    </div>

    <!-- Footer -->
    <footer class="border-t border-border-light py-6 px-6 lg:px-8">
      <div class="max-w-5xl mx-auto flex items-center justify-between">
        <span class="text-xs text-muted">&copy; {{ new Date().getFullYear() }} AgentCheck</span>
        <div class="flex items-center gap-5 text-xs text-muted">
          <router-link to="/privacy" class="hover:text-secondary transition-colors">Privacy Policy</router-link>
          <router-link to="/terms" class="hover:text-secondary transition-colors">Terms of Service</router-link>
          <router-link to="/imprint" class="hover:text-secondary transition-colors">Imprint</router-link>
          <a
            href="https://github.com/lennystepn-hue/agentready"
            target="_blank"
            rel="noopener"
            class="hover:text-secondary transition-colors"
          >
            GitHub
          </a>
        </div>
      </div>
    </footer>
  </div>
</template>
