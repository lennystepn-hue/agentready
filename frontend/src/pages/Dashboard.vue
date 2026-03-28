<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { isLoggedIn, isPro, user, logout } from '../auth.js'
import { getUserScans, getMonitors } from '../api.js'

const router = useRouter()

const scans = ref([])
const monitors = ref([])
const loadingScans = ref(true)
const loadingMonitors = ref(false)
const error = ref('')

function gradeFor(score) {
  if (score >= 90) return 'A+'
  if (score >= 80) return 'A'
  if (score >= 70) return 'B'
  if (score >= 60) return 'C'
  if (score >= 40) return 'D'
  return 'F'
}

function scoreColorClass(score) {
  if (score >= 70) return 'text-score-good'
  if (score >= 40) return 'text-score-medium'
  return 'text-score-bad'
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric',
  })
}

function handleLogout() {
  logout()
  router.push('/')
}

onMounted(async () => {
  try {
    scans.value = await getUserScans()
  } catch (e) {
    error.value = e.message || 'Could not load scans.'
  } finally {
    loadingScans.value = false
  }

  if (isPro.value) {
    loadingMonitors.value = true
    try {
      monitors.value = await getMonitors()
    } catch {
      // non-critical
    } finally {
      loadingMonitors.value = false
    }
  }
})
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
      <!-- Header -->
      <div class="border-b border-border-light bg-warm-50">
        <div class="max-w-5xl mx-auto px-6 lg:px-8 py-10 animate-fade-in">
          <div class="flex items-center gap-4">
            <div>
              <h1 class="font-display text-2xl font-bold tracking-tight text-primary">Welcome back</h1>
              <div class="flex items-center gap-3 mt-1.5">
                <span class="text-sm text-secondary">{{ user?.email }}</span>
                <span
                  class="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-display font-bold uppercase tracking-wider"
                  :class="isPro ? 'bg-accent-light text-accent' : 'bg-warm-100 text-muted'"
                >
                  {{ isPro ? 'Pro' : 'Free' }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="max-w-5xl mx-auto px-6 lg:px-8 py-10">

        <!-- Quick actions -->
        <section class="mb-10 animate-slide-up">
          <p class="section-label mb-4">Quick actions</p>
          <div class="flex flex-wrap gap-3">
            <router-link to="/" class="btn-primary">Run new scan</router-link>
            <router-link to="/compare" class="btn-secondary">Compare competitors</router-link>
            <router-link to="/monitoring" class="btn-secondary">View monitoring</router-link>
          </div>
        </section>

        <!-- Recent scans -->
        <section class="mb-10 animate-slide-up" style="animation-delay: 80ms">
          <p class="section-label mb-4">Recent scans</p>

          <div v-if="loadingScans" class="py-8 text-center">
            <svg class="w-5 h-5 text-accent animate-spin mx-auto mb-2" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            <p class="text-sm text-muted">Loading scans...</p>
          </div>

          <div v-else-if="error" class="py-8 text-center">
            <p class="text-sm text-score-bad">{{ error }}</p>
          </div>

          <div v-else-if="scans.length === 0" class="border border-border-light rounded-lg p-8 text-center">
            <p class="text-sm text-secondary mb-3">No scans yet. Run your first scan to see results here.</p>
            <router-link to="/" class="btn-primary">Run a scan</router-link>
          </div>

          <div v-else class="border border-border rounded-lg overflow-hidden bg-surface">
            <div
              v-for="(scan, idx) in scans"
              :key="scan.scan_id || idx"
              class="flex items-center gap-4 px-5 py-3.5 border-b border-border-light last:border-b-0 hover:bg-warm-50 transition-colors"
            >
              <div class="flex-shrink-0">
                <span
                  class="font-display font-bold text-lg tabular-nums"
                  :class="scoreColorClass(scan.score)"
                >
                  {{ scan.score }}
                </span>
              </div>
              <div class="flex-1 min-w-0">
                <p class="text-sm font-display font-semibold text-primary truncate">{{ scan.domain }}</p>
                <p class="text-xs text-muted">
                  Grade {{ scan.grade || gradeFor(scan.score) }}
                  <span v-if="scan.created_at"> &middot; {{ formatDate(scan.created_at) }}</span>
                </p>
              </div>
              <router-link
                :to="{ name: 'Report', params: { id: scan.scan_id } }"
                class="btn-ghost text-[13px] flex-shrink-0"
              >
                View report
              </router-link>
            </div>
          </div>
        </section>

        <!-- Pro monitoring summary or upgrade CTA -->
        <section class="animate-slide-up" style="animation-delay: 160ms">
          <div v-if="isPro && monitors.length > 0" class="mb-10">
            <p class="section-label mb-4">Monitored domains</p>
            <div class="border border-border rounded-lg overflow-hidden bg-surface">
              <div
                v-for="mon in monitors"
                :key="mon.id"
                class="flex items-center gap-4 px-5 py-3.5 border-b border-border-light last:border-b-0"
              >
                <div class="flex-1 min-w-0">
                  <p class="text-sm font-display font-semibold text-primary truncate">{{ mon.domain }}</p>
                  <p class="text-xs text-muted">
                    Last score: <span class="font-display font-semibold" :class="scoreColorClass(mon.last_score || 0)">{{ mon.last_score ?? '---' }}</span>
                    <span v-if="mon.last_scan_at"> &middot; {{ formatDate(mon.last_scan_at) }}</span>
                  </p>
                </div>
                <router-link
                  :to="{ name: 'History', params: { domain: mon.domain } }"
                  class="btn-ghost text-[13px]"
                >
                  View history
                </router-link>
              </div>
            </div>
          </div>

          <div v-if="!isPro" class="border border-accent/20 rounded-lg p-6 bg-accent/[0.03]">
            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <h3 class="font-display font-semibold text-primary">Unlock Pro features</h3>
                <p class="text-sm text-secondary mt-1 leading-relaxed">
                  Get competitor comparisons, weekly monitoring, score history, unlimited fix files, and priority support.
                </p>
              </div>
              <router-link to="/pricing" class="btn-primary flex-shrink-0">
                View plans
              </router-link>
            </div>
          </div>
        </section>
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
