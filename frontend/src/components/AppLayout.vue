<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { isLoggedIn, isPro, user, logout } from '../auth.js'
import { createBillingPortal } from '../api.js'

const route = useRoute()
const router = useRouter()

function handleLogout() {
  logout()
  router.push('/')
}

async function handleManageSubscription() {
  try {
    const data = await createBillingPortal()
    if (data.portal_url) {
      window.location.href = data.portal_url
    }
  } catch (e) {
    // fallback: go to pricing
    router.push('/pricing')
  }
}

const navLinks = computed(() => [
  {
    to: '/dashboard',
    label: 'Dashboard',
    icon: 'dashboard',
    requiresPro: false,
  },
  {
    to: '/',
    label: 'Run scan',
    icon: 'scan',
    requiresPro: false,
  },
  {
    to: '/compare',
    label: 'Compare',
    icon: 'compare',
    requiresPro: true,
  },
  {
    to: '/monitoring',
    label: 'Monitoring',
    icon: 'monitoring',
    requiresPro: true,
  },
  {
    to: '/history',
    label: 'History',
    icon: 'history',
    requiresPro: true,
  },
])

function isActive(to) {
  if (to === '/') return route.path === '/'
  return route.path.startsWith(to)
}
</script>

<template>
  <div class="flex-1 flex flex-col min-h-screen">
    <!-- Top nav bar -->
    <nav class="sticky top-0 z-50 bg-page/95 backdrop-blur-sm border-b border-border-light">
      <div class="px-6 lg:px-8 h-14 flex items-center justify-between">
        <router-link to="/" class="flex items-center gap-2">
          <svg class="w-5 h-5 text-accent" viewBox="0 0 24 24" fill="none">
            <path d="M12 2L4 20h4l1.5-4h5L16 20h4L12 2zm0 7l2 5h-4l2-5z" fill="currentColor"/>
            <path d="M20 8a10 10 0 00-4-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" opacity="0.5"/>
            <path d="M22 6a14 14 0 00-6-5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" opacity="0.3"/>
          </svg>
          <span class="font-display font-bold text-[15px] tracking-tight">AgentCheck</span>
        </router-link>
        <div class="flex items-center gap-4">
          <div
            class="w-7 h-7 rounded-full bg-accent text-white flex items-center justify-center text-xs font-display font-bold"
            :title="user?.email"
          >
            {{ user?.email?.[0]?.toUpperCase() || '?' }}
          </div>
        </div>
      </div>
    </nav>

    <div class="flex flex-1">
      <!-- Sidebar (hidden on mobile) -->
      <aside class="hidden sm:flex flex-col w-56 flex-shrink-0 border-r border-border-light bg-warm-50">
        <div class="flex-1 py-4 px-3 overflow-y-auto">
          <!-- Main nav links -->
          <nav class="space-y-0.5">
            <router-link
              v-for="link in navLinks"
              :key="link.to"
              :to="link.to"
              class="flex items-center gap-2.5 text-sm py-2 px-3 rounded-md transition-colors"
              :class="isActive(link.to)
                ? 'bg-accent/10 text-accent font-semibold'
                : 'text-secondary hover:bg-warm-100 hover:text-primary'"
            >
              <!-- Dashboard icon -->
              <svg v-if="link.icon === 'dashboard'" class="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zm10 0a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zm10 0a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
              </svg>
              <!-- Scan icon -->
              <svg v-if="link.icon === 'scan'" class="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <!-- Compare icon -->
              <svg v-if="link.icon === 'compare'" class="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7m0 10a2 2 0 002 2h2a2 2 0 002-2V7a2 2 0 00-2-2h-2a2 2 0 00-2 2" />
              </svg>
              <!-- Monitoring icon -->
              <svg v-if="link.icon === 'monitoring'" class="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
              </svg>
              <!-- History icon -->
              <svg v-if="link.icon === 'history'" class="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>

              <span class="flex-1">{{ link.label }}</span>
              <span
                v-if="link.requiresPro && !isPro"
                class="text-[10px] bg-warm-200 text-warm-600 px-1.5 rounded font-display"
              >Pro</span>
            </router-link>
          </nav>

          <!-- Divider -->
          <div class="border-t border-border-light my-3"></div>

          <!-- Secondary links -->
          <nav class="space-y-0.5">
            <router-link
              to="/pricing"
              class="flex items-center gap-2.5 text-sm py-2 px-3 rounded-md transition-colors"
              :class="isActive('/pricing')
                ? 'bg-accent/10 text-accent font-semibold'
                : 'text-secondary hover:bg-warm-100 hover:text-primary'"
            >
              <svg class="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A2 2 0 013 12V7a4 4 0 014-4z" />
              </svg>
              <span>Pricing</span>
            </router-link>
            <button
              v-if="isPro"
              @click="handleManageSubscription"
              class="w-full flex items-center gap-2.5 text-sm py-2 px-3 rounded-md text-secondary hover:bg-warm-100 hover:text-primary transition-colors text-left"
            >
              <svg class="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              <span>Manage subscription</span>
            </button>
          </nav>

          <!-- Divider -->
          <div class="border-t border-border-light my-3"></div>

          <!-- Sign out -->
          <button
            @click="handleLogout"
            class="w-full flex items-center gap-2.5 text-sm py-2 px-3 rounded-md text-secondary hover:bg-warm-100 hover:text-primary transition-colors text-left"
          >
            <svg class="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
            <span>Sign out</span>
          </button>
        </div>

        <!-- Legal links -->
        <div class="px-3 py-3 border-t border-border-light">
          <div class="flex flex-wrap gap-x-3 gap-y-1 px-3">
            <router-link to="/privacy" class="text-[11px] text-muted hover:text-secondary transition-colors">Privacy</router-link>
            <router-link to="/terms" class="text-[11px] text-muted hover:text-secondary transition-colors">Terms</router-link>
            <router-link to="/imprint" class="text-[11px] text-muted hover:text-secondary transition-colors">Imprint</router-link>
          </div>
        </div>

        <!-- User info at bottom -->
        <div class="px-3 py-3 border-t border-border-light">
          <div class="flex items-center gap-2.5 px-3">
            <div
              class="w-7 h-7 rounded-full bg-accent text-white flex items-center justify-center text-xs font-display font-bold flex-shrink-0"
            >
              {{ user?.email?.[0]?.toUpperCase() || '?' }}
            </div>
            <div class="min-w-0">
              <p class="text-xs text-primary font-display font-medium truncate">{{ user?.email }}</p>
              <p class="text-[10px] font-display uppercase tracking-wider" :class="isPro ? 'text-accent' : 'text-muted'">
                {{ isPro ? 'Pro plan' : 'Free plan' }}
              </p>
            </div>
          </div>
        </div>
      </aside>

      <!-- Main content area -->
      <main class="flex-1 flex flex-col min-w-0">
        <slot />
      </main>
    </div>

    <!-- Mobile bottom nav -->
    <div class="sm:hidden fixed bottom-0 left-0 right-0 z-50 bg-page/95 backdrop-blur-sm border-t border-border-light">
      <nav class="flex items-center justify-around h-14 px-2">
        <router-link
          to="/dashboard"
          class="flex flex-col items-center gap-0.5 py-1 px-2 rounded-md transition-colors"
          :class="isActive('/dashboard') ? 'text-accent' : 'text-muted'"
        >
          <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zm10 0a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zm10 0a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
          </svg>
          <span class="text-[10px] font-display">Dashboard</span>
        </router-link>

        <router-link
          to="/"
          class="flex flex-col items-center gap-0.5 py-1 px-2 rounded-md transition-colors"
          :class="route.path === '/' ? 'text-accent' : 'text-muted'"
        >
          <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <span class="text-[10px] font-display">Scan</span>
        </router-link>

        <router-link
          to="/compare"
          class="flex flex-col items-center gap-0.5 py-1 px-2 rounded-md transition-colors"
          :class="isActive('/compare') ? 'text-accent' : 'text-muted'"
        >
          <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7m0 10a2 2 0 002 2h2a2 2 0 002-2V7a2 2 0 00-2-2h-2a2 2 0 00-2 2" />
          </svg>
          <span class="text-[10px] font-display">Compare</span>
        </router-link>

        <router-link
          to="/monitoring"
          class="flex flex-col items-center gap-0.5 py-1 px-2 rounded-md transition-colors"
          :class="isActive('/monitoring') ? 'text-accent' : 'text-muted'"
        >
          <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
          </svg>
          <span class="text-[10px] font-display">Monitor</span>
        </router-link>

        <button
          @click="handleLogout"
          class="flex flex-col items-center gap-0.5 py-1 px-2 rounded-md text-muted transition-colors"
        >
          <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
          </svg>
          <span class="text-[10px] font-display">Sign out</span>
        </button>
      </nav>
    </div>
  </div>
</template>
