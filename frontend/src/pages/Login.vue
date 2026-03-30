<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { isLoggedIn } from '../auth.js'
import { login, register } from '../auth.js'
import AppHeader from '../components/AppHeader.vue'

const router = useRouter()
const route = useRoute()

const mode = ref('login')
const email = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')
const emailError = ref('')
const passwordError = ref('')

function switchMode(m) {
  mode.value = m
  error.value = ''
  emailError.value = ''
  passwordError.value = ''
}

async function handleSubmit() {
  error.value = ''
  emailError.value = ''
  passwordError.value = ''
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
    const msg = e.message || 'Something went wrong. Please try again.'
    // Route errors to field-level where possible
    if (msg.toLowerCase().includes('email') || msg.toLowerCase().includes('user')) {
      emailError.value = msg
    } else if (msg.toLowerCase().includes('password')) {
      passwordError.value = msg
    } else {
      error.value = msg
    }
  } finally {
    loading.value = false
  }
}

// Redirect if already logged in
if (isLoggedIn.value) {
  router.replace(route.query.redirect || '/dashboard')
}

const benefits = [
  {
    icon: `<path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" stroke-linecap="round" stroke-linejoin="round"/>`,
    title: 'Save scan history',
    desc: 'Track your AI-readiness score over time and see how improvements land.',
  },
  {
    icon: `<path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" stroke-linecap="round" stroke-linejoin="round"/>`,
    title: 'Download fix files',
    desc: 'Get ready-to-deploy llms.txt, ai.txt, and schema patches for every issue found.',
  },
  {
    icon: `<path d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" stroke-linecap="round" stroke-linejoin="round"/>`,
    title: 'Monitor competitors',
    desc: 'Compare your score side-by-side with up to 3 competitor domains.',
  },
]
</script>

<template>
  <div class="flex-1 flex flex-col min-h-0">
    <AppHeader show-back="/" back-label="Home" />

    <div class="flex-1 flex min-h-0">
      <!-- Left: form panel -->
      <div class="flex-1 flex items-start justify-center px-6 lg:px-12 py-14 sm:py-20 lg:max-w-[520px]">
        <div class="w-full max-w-sm animate-fade-in">

          <!-- Segmented mode toggle -->
          <div class="flex gap-0.5 mb-9 bg-warm-100 rounded-lg p-1" role="tablist" aria-label="Account mode">
            <button
              @click="switchMode('login')"
              role="tab"
              :aria-selected="mode === 'login'"
              class="flex-1 py-2 text-sm font-display font-semibold rounded-md transition-all duration-200"
              :class="mode === 'login'
                ? 'bg-surface text-primary shadow-sm'
                : 'text-secondary hover:text-primary'"
            >
              Sign in
            </button>
            <button
              @click="switchMode('register')"
              role="tab"
              :aria-selected="mode === 'register'"
              class="flex-1 py-2 text-sm font-display font-semibold rounded-md transition-all duration-200"
              :class="mode === 'register'
                ? 'bg-surface text-primary shadow-sm'
                : 'text-secondary hover:text-primary'"
            >
              Create account
            </button>
          </div>

          <!-- Heading -->
          <div class="mb-7">
            <h1 class="font-display text-[22px] font-bold tracking-tight text-primary leading-snug">
              {{ mode === 'login' ? 'Welcome back' : 'Start for free' }}
            </h1>
            <p class="text-sm text-secondary mt-1">
              {{ mode === 'login'
                ? 'Sign in to access your reports and fix files.'
                : 'Create an account to save history and unlock fix files.' }}
            </p>
          </div>

          <!-- Form -->
          <form @submit.prevent="handleSubmit" class="space-y-4" novalidate>
            <!-- Email field -->
            <div>
              <label for="email" class="block text-[13px] font-display font-medium text-primary mb-1.5">
                Email address
              </label>
              <input
                id="email"
                v-model="email"
                type="email"
                required
                autocomplete="email"
                placeholder="you@example.com"
                :disabled="loading"
                :class="[
                  'input-field text-sm',
                  emailError ? 'border-score-bad focus:border-score-bad focus:ring-score-bad/20' : ''
                ]"
                :aria-describedby="emailError ? 'email-error' : undefined"
                :aria-invalid="!!emailError"
              />
              <p v-if="emailError" id="email-error" class="mt-1.5 text-xs text-score-bad leading-snug" role="alert">
                {{ emailError }}
              </p>
            </div>

            <!-- Password field -->
            <div>
              <label for="password" class="block text-[13px] font-display font-medium text-primary mb-1.5">
                Password
              </label>
              <input
                id="password"
                v-model="password"
                type="password"
                required
                :autocomplete="mode === 'login' ? 'current-password' : 'new-password'"
                placeholder="&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;"
                :disabled="loading"
                :class="[
                  'input-field text-sm',
                  passwordError ? 'border-score-bad focus:border-score-bad focus:ring-score-bad/20' : ''
                ]"
                :aria-describedby="passwordError ? 'password-error' : undefined"
                :aria-invalid="!!passwordError"
              />
              <p v-if="passwordError" id="password-error" class="mt-1.5 text-xs text-score-bad leading-snug" role="alert">
                {{ passwordError }}
              </p>
            </div>

            <!-- Generic error -->
            <p v-if="error" class="text-xs text-score-bad leading-snug py-0.5" role="alert">
              {{ error }}
            </p>

            <!-- Submit -->
            <button
              type="submit"
              class="btn-primary w-full mt-1"
              :disabled="loading || !email.trim() || !password.trim()"
            >
              <svg
                v-if="loading"
                class="w-4 h-4 mr-2 animate-spin flex-shrink-0"
                fill="none"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              {{ loading
                ? (mode === 'login' ? 'Signing in...' : 'Creating account...')
                : (mode === 'login' ? 'Sign in' : 'Create account') }}
            </button>
          </form>

          <!-- Skip prompt -->
          <div class="mt-6 pt-5 border-t border-border-light text-center">
            <router-link
              to="/"
              class="text-[13px] text-muted hover:text-secondary transition-colors"
            >
              Continue without an account &rarr;
            </router-link>
          </div>

          <p class="mt-4 text-xs text-muted text-center leading-relaxed">
            Free forever. No credit card required.
          </p>
        </div>
      </div>

      <!-- Right: value proposition (lg+ only) -->
      <div class="hidden lg:flex flex-1 flex-col justify-center bg-warm-50 border-l border-border-light px-12 py-20 relative overflow-hidden">
        <!-- Concentric rings decorative motif -->
        <div class="absolute right-0 top-1/2 -translate-y-1/2 translate-x-1/3 pointer-events-none" aria-hidden="true">
          <div class="relative w-[480px] h-[480px]">
            <div class="absolute inset-0 rounded-full border border-warm-200/60"></div>
            <div class="absolute inset-[15%] rounded-full border border-warm-200/50"></div>
            <div class="absolute inset-[30%] rounded-full border border-warm-200/40"></div>
            <div class="absolute inset-[45%] rounded-full border border-warm-300/40"></div>
            <div class="absolute inset-[58%] rounded-full border border-warm-300/50"></div>
            <!-- Accent dot at center -->
            <div class="absolute inset-[50%] -translate-x-1/2 -translate-y-1/2 w-4 h-4 rounded-full bg-accent/20"></div>
          </div>
        </div>

        <!-- Content -->
        <div class="relative z-10 max-w-xs">
          <p class="section-label mb-6">Why sign in</p>

          <div class="space-y-7">
            <div
              v-for="(benefit, i) in benefits"
              :key="i"
              class="flex items-start gap-4 animate-slide-up"
              :style="{ animationDelay: `${i * 80}ms` }"
            >
              <!-- Icon -->
              <div class="flex-shrink-0 w-9 h-9 rounded-lg bg-accent/10 flex items-center justify-center mt-0.5">
                <svg
                  class="w-[18px] h-[18px] text-accent"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  stroke-width="1.6"
                  v-html="benefit.icon"
                />
              </div>
              <!-- Text -->
              <div>
                <p class="text-sm font-display font-semibold text-primary leading-snug">{{ benefit.title }}</p>
                <p class="text-[13px] text-secondary mt-0.5 leading-relaxed">{{ benefit.desc }}</p>
              </div>
            </div>
          </div>

          <!-- Score sample -->
          <div class="mt-10 p-4 bg-surface rounded-xl border border-border-light">
            <div class="flex items-center justify-between mb-3">
              <span class="text-xs font-display font-semibold text-muted uppercase tracking-wider">AI Readiness Score</span>
              <span class="text-xs text-secondary">example.com</span>
            </div>
            <div class="flex items-end gap-3">
              <span class="font-display text-3xl font-bold text-primary tabular-nums">73</span>
              <span class="text-sm text-secondary mb-1">/ 100</span>
              <span class="ml-auto text-xs font-display font-semibold text-score-medium bg-score-medium/10 px-2 py-0.5 rounded-full">Needs work</span>
            </div>
            <div class="mt-3 h-1.5 bg-warm-100 rounded-full overflow-hidden">
              <div class="h-full rounded-full bg-score-medium" style="width: 73%"></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Footer -->
    <footer class="border-t border-border-light py-5 px-6 lg:px-8 flex-shrink-0">
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
