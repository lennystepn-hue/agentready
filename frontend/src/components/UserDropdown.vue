<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { user, isPro, logout } from '../auth.js'
import { createBillingPortal } from '../api.js'

const router = useRouter()
const open = ref(false)
const dropdownRef = ref(null)
const triggerRef = ref(null)

function toggle() {
  open.value = !open.value
}

function close() {
  open.value = false
}

function onClickOutside(e) {
  if (
    dropdownRef.value &&
    !dropdownRef.value.contains(e.target) &&
    triggerRef.value &&
    !triggerRef.value.contains(e.target)
  ) {
    close()
  }
}

function navigate(path) {
  close()
  router.push(path)
}

async function handleBilling() {
  close()
  try {
    const data = await createBillingPortal()
    const url = data.portal_url || data.url
    if (url) window.location.href = url
  } catch {
    // Billing portal error handled silently
  }
}

function handleSignOut() {
  close()
  logout()
}

// Register/unregister click-outside listener
import { onMounted, onBeforeUnmount } from 'vue'

onMounted(() => {
  document.addEventListener('click', onClickOutside)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', onClickOutside)
})

const initial = () => {
  if (!user.value?.email) return '?'
  return user.value.email.charAt(0).toUpperCase()
}
</script>

<template>
  <div class="relative">
    <button
      ref="triggerRef"
      @click="toggle"
      class="w-8 h-8 shrink-0 rounded-full bg-accent text-white flex items-center justify-center text-sm font-semibold font-display leading-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 transition-transform hover:scale-105"
      :aria-expanded="open"
      aria-haspopup="true"
    >
      {{ initial() }}
    </button>

    <Transition
      enter-active-class="transition ease-out duration-150"
      enter-from-class="opacity-0 -translate-y-1"
      enter-to-class="opacity-100 translate-y-0"
      leave-active-class="transition ease-in duration-100"
      leave-from-class="opacity-100 translate-y-0"
      leave-to-class="opacity-0 -translate-y-1"
    >
      <div
        v-if="open"
        ref="dropdownRef"
        class="absolute right-0 mt-2 w-64 max-w-[calc(100vw-2rem)] bg-surface border border-border-light rounded-lg shadow-lg z-[999] overflow-hidden"
      >
        <!-- User info -->
        <div class="px-4 py-3 border-b border-border-light">
          <p class="text-sm text-warm-800 truncate font-body">{{ user?.email }}</p>
          <span
            v-if="isPro"
            class="mt-1 inline-block text-xs font-semibold px-2 py-0.5 rounded-full bg-accent text-white"
          >
            Pro
          </span>
          <span
            v-else
            class="mt-1 inline-block text-xs font-semibold px-2 py-0.5 rounded-full bg-warm-200 text-warm-600"
          >
            Free
          </span>
        </div>

        <!-- Menu items -->
        <div class="py-1">
          <button
            @click="navigate('/dashboard')"
            class="w-full flex items-center gap-3 px-4 py-2 text-sm text-warm-700 hover:bg-warm-50 transition-colors text-left"
          >
            <svg class="w-4 h-4 text-warm-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="3" y="3" width="7" height="7" rx="1" />
              <rect x="14" y="3" width="7" height="7" rx="1" />
              <rect x="3" y="14" width="7" height="7" rx="1" />
              <rect x="14" y="14" width="7" height="7" rx="1" />
            </svg>
            Dashboard
          </button>

          <button
            @click="navigate('/pricing')"
            class="w-full flex items-center gap-3 px-4 py-2 text-sm text-warm-700 hover:bg-warm-50 transition-colors text-left"
          >
            <svg class="w-4 h-4 text-warm-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 2v20M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6" />
            </svg>
            <template v-if="isPro">Pricing</template>
            <template v-else>Upgrade to Pro</template>
          </button>

          <button
            v-if="isPro"
            @click="handleBilling"
            class="w-full flex items-center gap-3 px-4 py-2 text-sm text-warm-700 hover:bg-warm-50 transition-colors text-left"
          >
            <svg class="w-4 h-4 text-warm-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="1" y="4" width="22" height="16" rx="2" />
              <line x1="1" y1="10" x2="23" y2="10" />
            </svg>
            Manage billing
          </button>
        </div>

        <!-- Sign out -->
        <div class="border-t border-border-light py-1">
          <button
            @click="handleSignOut"
            class="w-full flex items-center gap-3 px-4 py-2 text-sm text-warm-700 hover:bg-warm-50 transition-colors text-left"
          >
            <svg class="w-4 h-4 text-warm-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4" />
              <polyline points="16 17 21 12 16 7" />
              <line x1="21" y1="12" x2="9" y2="12" />
            </svg>
            Sign out
          </button>
        </div>
      </div>
    </Transition>
  </div>
</template>
