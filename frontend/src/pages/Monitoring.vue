<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { isLoggedIn, isPro, user, logout } from '../auth.js'
import { getMonitors, addMonitor, removeMonitor } from '../api.js'

const router = useRouter()

const monitors = ref([])
const newDomain = ref('')
const loading = ref(true)
const adding = ref(false)
const error = ref('')
const addError = ref('')

function handleLogout() {
  logout()
  router.push('/')
}

function scoreColorClass(score) {
  if (score >= 70) return 'text-score-good'
  if (score >= 40) return 'text-score-medium'
  return 'text-score-bad'
}

function formatDate(dateStr) {
  if (!dateStr) return '---'
  return new Date(dateStr).toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric',
  })
}

async function fetchMonitors() {
  try {
    monitors.value = await getMonitors()
  } catch (e) {
    error.value = e.message || 'Could not load monitors.'
  } finally {
    loading.value = false
  }
}

async function handleAdd() {
  const domain = newDomain.value.trim()
  if (!domain) return

  addError.value = ''
  adding.value = true
  try {
    const mon = await addMonitor(domain)
    monitors.value.push(mon)
    newDomain.value = ''
  } catch (e) {
    addError.value = e.message || 'Could not add domain.'
  } finally {
    adding.value = false
  }
}

async function handleRemove(id) {
  try {
    await removeMonitor(id)
    monitors.value = monitors.value.filter(m => m.id !== id)
  } catch (e) {
    error.value = e.message || 'Could not remove domain.'
  }
}

onMounted(fetchMonitors)
</script>

<template>
  <div class="flex-1 flex flex-col">
    <!-- Nav -->
    <nav class="sticky top-0 z-50 bg-page/95 backdrop-blur-sm border-b border-border-light">
      <div class="max-w-5xl mx-auto px-6 lg:px-8 h-14 flex items-center justify-between">
        <router-link to="/" class="flex items-center gap-2">
          <svg class="w-5 h-5 text-accent" viewBox="0 0 24 24" fill="none">
            <path d="M12 2L4 20h4l1.5-4h5L16 20h4L12 2zm0 7l2 5h-4l2-5z" fill="currentColor"/>
            <path d="M20 8a10 10 0 00-4-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" opacity="0.5"/>
            <path d="M22 6a14 14 0 00-6-5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" opacity="0.3"/>
          </svg>
          <span class="font-display font-bold text-[15px] tracking-tight">AgentReady</span>
        </router-link>
        <div class="flex items-center gap-4">
          <router-link to="/dashboard" class="text-[13px] text-secondary hover:text-primary transition-colors">Dashboard</router-link>
          <router-link to="/pricing" class="text-[13px] text-secondary hover:text-primary transition-colors">Pricing</router-link>
          <button @click="handleLogout" class="btn-ghost text-[13px]">Sign out</button>
          <div
            class="w-7 h-7 rounded-full bg-accent text-white flex items-center justify-center text-xs font-display font-bold"
            :title="user?.email"
          >
            {{ user?.email?.[0]?.toUpperCase() || '?' }}
          </div>
        </div>
      </div>
    </nav>

    <!-- Content -->
    <div class="flex-1">
      <div class="max-w-5xl mx-auto px-6 lg:px-8 py-10">

        <div class="animate-fade-in mb-8">
          <p class="section-label mb-2">Pro feature</p>
          <h1 class="font-display text-2xl font-bold tracking-tight text-primary">Domain monitoring</h1>
          <p class="text-sm text-secondary mt-2 leading-relaxed max-w-lg">
            Track your AI agent readiness score over time. We scan your monitored domains weekly and alert you to changes.
          </p>
        </div>

        <!-- Pro gate -->
        <div v-if="!isPro" class="border border-accent/20 rounded-lg p-8 bg-accent/[0.03] text-center animate-slide-up">
          <h3 class="font-display font-semibold text-primary mb-2">Pro feature</h3>
          <p class="text-sm text-secondary mb-4 max-w-sm mx-auto">
            Domain monitoring is available on the Pro plan. Upgrade to automatically track your score over time.
          </p>
          <router-link to="/pricing" class="btn-primary">Upgrade to Pro</router-link>
        </div>

        <!-- Monitoring content -->
        <div v-else class="animate-slide-up">
          <!-- Add domain form -->
          <form @submit.prevent="handleAdd" class="flex gap-3 max-w-md mb-8">
            <input
              v-model="newDomain"
              type="text"
              placeholder="domain-to-monitor.com"
              class="input-field flex-1"
              :disabled="adding"
            />
            <button
              type="submit"
              class="btn-primary whitespace-nowrap"
              :disabled="adding || !newDomain.trim()"
            >
              {{ adding ? 'Adding...' : 'Add domain' }}
            </button>
          </form>
          <p v-if="addError" class="text-sm text-score-bad mb-4 -mt-4">{{ addError }}</p>

          <!-- Loading -->
          <div v-if="loading" class="py-8 text-center">
            <svg class="w-5 h-5 text-accent animate-spin mx-auto mb-2" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            <p class="text-sm text-muted">Loading monitors...</p>
          </div>

          <div v-else-if="error" class="py-8 text-center">
            <p class="text-sm text-score-bad">{{ error }}</p>
          </div>

          <!-- Empty state -->
          <div v-else-if="monitors.length === 0" class="border border-border-light rounded-lg p-8 text-center">
            <p class="text-sm text-secondary">No domains monitored yet. Add one above to get started.</p>
          </div>

          <!-- Monitor list -->
          <div v-else class="border border-border rounded-lg overflow-hidden bg-surface">
            <div
              v-for="mon in monitors"
              :key="mon.id"
              class="flex items-center gap-4 px-5 py-3.5 border-b border-border-light last:border-b-0"
            >
              <div class="flex-1 min-w-0">
                <p class="text-sm font-display font-semibold text-primary truncate">{{ mon.domain }}</p>
                <p class="text-xs text-muted">
                  Last score:
                  <span class="font-display font-semibold" :class="scoreColorClass(mon.last_score || 0)">
                    {{ mon.last_score ?? '---' }}
                  </span>
                  &middot; Last scanned: {{ formatDate(mon.last_scan_at) }}
                </p>
              </div>
              <router-link
                :to="{ name: 'History', params: { domain: mon.domain } }"
                class="btn-ghost text-[13px]"
              >
                History
              </router-link>
              <button
                @click="handleRemove(mon.id)"
                class="btn-ghost text-[13px] text-score-bad hover:text-score-bad"
                title="Remove monitoring"
              >
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Footer -->
    <footer class="border-t border-border-light py-6 px-6 lg:px-8 mt-auto">
      <div class="max-w-5xl mx-auto flex items-center justify-between">
        <span class="text-xs text-muted">&copy; {{ new Date().getFullYear() }} AgentReady</span>
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
