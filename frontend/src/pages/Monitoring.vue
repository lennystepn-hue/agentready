<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { isLoggedIn, isPro, user, logout } from '../auth.js'
import { getMonitors, addMonitor, removeMonitor, getUserScans } from '../api.js'
import AppLayout from '../components/AppLayout.vue'

const router = useRouter()

const monitors = ref([])
const allScans = ref([])
const newDomain = ref('')
const loading = ref(true)
const adding = ref(false)
const error = ref('')
const addError = ref('')
const showSuggestions = ref(false)

function gradeFor(score) {
  if (score >= 90) return 'A+'
  if (score >= 80) return 'A'
  if (score >= 70) return 'B'
  if (score >= 60) return 'C'
  if (score >= 40) return 'D'
  return 'F'
}

function normalizeScan(s) {
  return {
    scan_id: s.scan_id || s.id,
    domain: s.domain || '',
    score: s.score ?? s.total_score ?? null,
    grade: s.grade || gradeFor(s.score ?? s.total_score ?? null),
    status: s.status || 'unknown',
    created_at: s.created_at || s.completed_at || '',
  }
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

// Unique scanned domains not already monitored
const monitoredDomains = computed(() => new Set(monitors.value.map(m => m.domain)))

const scannedDomains = computed(() => {
  const seen = new Set()
  const result = []
  for (const s of allScans.value) {
    if (s.domain && !seen.has(s.domain)) {
      seen.add(s.domain)
      result.push(s)
    }
  }
  return result
})

const unmonitoredScans = computed(() =>
  scannedDomains.value.filter(s => !monitoredDomains.value.has(s.domain))
)

// Filtered suggestions for the input autocomplete
const domainSuggestions = computed(() => {
  const query = newDomain.value.trim().toLowerCase()
  return scannedDomains.value
    .filter(s => !monitoredDomains.value.has(s.domain))
    .filter(s => !query || s.domain.toLowerCase().includes(query))
    .slice(0, 5)
})

// Most recent completed scan per domain for showing scores
const latestScanByDomain = computed(() => {
  const map = {}
  for (const s of allScans.value) {
    if (s.status !== 'completed' || !s.domain) continue
    if (!map[s.domain] || new Date(s.created_at) > new Date(map[s.domain].created_at)) {
      map[s.domain] = s
    }
  }
  return map
})

async function fetchMonitors() {
  try {
    const data = await getMonitors()
    monitors.value = Array.isArray(data) ? data : (data.monitors || [])
  } catch (e) {
    error.value = e.message || 'Could not load monitors.'
  }
}

async function fetchScans() {
  try {
    const data = await getUserScans()
    const raw = Array.isArray(data) ? data : (data.scans || [])
    allScans.value = raw.map(normalizeScan).sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
  } catch {
    // non-critical — suggestions just won't appear
  }
}

async function handleAdd(domainStr) {
  const domain = (domainStr || newDomain.value).trim()
  if (!domain) return

  addError.value = ''
  adding.value = true
  showSuggestions.value = false
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

function selectSuggestion(domain) {
  newDomain.value = domain
  showSuggestions.value = false
}

function handleInputFocus() {
  showSuggestions.value = true
}

function handleInputBlur() {
  // Delay to allow click on suggestion
  setTimeout(() => { showSuggestions.value = false }, 200)
}

onMounted(async () => {
  await Promise.all([fetchMonitors(), fetchScans()])
  loading.value = false
})
</script>

<template>
  <AppLayout>
    <div class="flex-1 pb-16 sm:pb-0">
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
          <div class="relative max-w-md mb-8">
            <form @submit.prevent="handleAdd()" class="flex gap-3">
              <div class="relative flex-1">
                <input
                  v-model="newDomain"
                  type="text"
                  placeholder="domain-to-monitor.com"
                  class="input-field w-full"
                  :disabled="adding"
                  @focus="handleInputFocus"
                  @blur="handleInputBlur"
                  @input="showSuggestions = true"
                />
                <!-- Domain suggestions -->
                <div
                  v-if="showSuggestions && domainSuggestions.length > 0"
                  class="absolute z-10 left-0 right-0 top-full mt-1 border border-border rounded-lg bg-surface shadow-lg overflow-hidden"
                >
                  <button
                    v-for="s in domainSuggestions"
                    :key="s.domain"
                    type="button"
                    @mousedown.prevent="selectSuggestion(s.domain)"
                    class="w-full text-left px-4 py-2.5 text-sm hover:bg-warm-100 transition-colors flex items-center justify-between gap-3"
                  >
                    <span class="font-display text-primary truncate">{{ s.domain }}</span>
                    <span v-if="s.score != null" class="text-xs font-display font-semibold tabular-nums shrink-0" :class="scoreColorClass(s.score)">
                      {{ s.score }}
                    </span>
                  </button>
                </div>
              </div>
              <button
                type="submit"
                class="btn-primary whitespace-nowrap"
                :disabled="adding || !newDomain.trim()"
              >
                {{ adding ? 'Adding...' : 'Add domain' }}
              </button>
            </form>
          </div>
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

          <template v-else>
            <!-- Monitor list -->
            <div v-if="monitors.length > 0" class="border border-border rounded-lg overflow-hidden bg-surface mb-8">
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
                  v-if="mon.last_score != null"
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

            <!-- Scanned domains not yet monitored — show as suggestions -->
            <div v-if="unmonitoredScans.length > 0">
              <p class="section-label mb-3">{{ monitors.length > 0 ? 'Add from your recent scans' : 'Your recent scans' }}</p>
              <p v-if="monitors.length === 0" class="text-sm text-secondary mb-4">
                No domains monitored yet. Add one from your recent scans or type a domain above.
              </p>
              <div class="border border-border rounded-lg overflow-hidden bg-surface">
                <div
                  v-for="s in unmonitoredScans"
                  :key="s.scan_id"
                  class="flex items-center gap-4 px-5 py-3.5 border-b border-border-light last:border-b-0"
                >
                  <div class="flex-1 min-w-0">
                    <p class="text-sm font-display font-semibold text-primary truncate">{{ s.domain }}</p>
                    <p class="text-xs text-muted">
                      Score:
                      <span v-if="s.score != null" class="font-display font-semibold" :class="scoreColorClass(s.score)">{{ s.score }}</span>
                      <span v-else>---</span>
                      &middot; {{ formatDate(s.created_at) }}
                    </p>
                  </div>
                  <router-link
                    v-if="s.scan_id && s.status === 'completed'"
                    :to="{ name: 'Report', params: { id: s.scan_id } }"
                    class="btn-ghost text-[13px]"
                  >
                    View report
                  </router-link>
                  <button
                    @click="handleAdd(s.domain)"
                    class="btn-primary text-[13px] !py-1.5 !px-3"
                    :disabled="adding"
                  >
                    Add to monitoring
                  </button>
                </div>
              </div>
            </div>

            <!-- Fully empty: no monitors, no scans -->
            <div v-else-if="monitors.length === 0" class="border border-border-light rounded-lg p-8 text-center">
              <p class="text-sm text-secondary mb-1">You haven't scanned any domains yet.</p>
              <p class="text-sm text-muted mb-4">Run a scan to get started, then add your domain to monitoring.</p>
              <router-link to="/" class="btn-primary inline-block">Run a scan</router-link>
            </div>
          </template>
        </div>
      </div>
    </div>
  </AppLayout>
</template>
