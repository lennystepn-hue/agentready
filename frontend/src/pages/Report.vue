<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getScanResult } from '../api.js'
import ScoreCircle from '../components/ScoreCircle.vue'
import CategoryBar from '../components/CategoryBar.vue'
import FixCard from '../components/FixCard.vue'
import CheckItem from '../components/CheckItem.vue'

const route = useRoute()
const router = useRouter()
const scanId = route.params.id

const scan = ref(null)
const loading = ref(true)
const error = ref('')
const showAllChecks = ref(false)
const copied = ref(false)

const categories = computed(() => {
  if (!scan.value?.categories) return []
  return [
    { key: 'protocol_readiness', name: 'Protokoll-Bereitschaft' },
    { key: 'structured_data', name: 'Strukturierte Daten' },
    { key: 'agent_accessibility', name: 'Agent-Zugänglichkeit' },
    { key: 'transaction_readiness', name: 'Transaktions-Bereitschaft' },
    { key: 'trust_signals', name: 'Vertrauens-Signale' },
  ].map(c => ({
    ...c,
    score: scan.value.categories[c.key]?.score ?? 0,
    maxScore: scan.value.categories[c.key]?.max_score ?? 100,
  }))
})

const topFixes = computed(() => {
  if (!scan.value?.fixes) return []
  return scan.value.fixes.slice(0, 5)
})

const allChecks = computed(() => {
  if (!scan.value?.checks) return []
  return scan.value.checks
})

async function fetchReport() {
  try {
    const result = await getScanResult(scanId)
    if (result.status !== 'completed') {
      router.push({ name: 'ScanProgress', params: { id: scanId } })
      return
    }
    scan.value = result
  } catch (e) {
    error.value = e.message || 'Bericht konnte nicht geladen werden.'
  } finally {
    loading.value = false
  }
}

function shareReport() {
  const url = window.location.href
  navigator.clipboard.writeText(url).then(() => {
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
  })
}

onMounted(fetchReport)
</script>

<template>
  <div class="flex-1 flex flex-col">
    <!-- Nav -->
    <nav class="border-b border-slate-800/50">
      <div class="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
        <router-link to="/" class="flex items-center gap-2">
          <div class="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center">
            <svg class="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <span class="font-bold text-lg">AgentReady</span>
        </router-link>
        <div class="flex items-center gap-3">
          <router-link
            :to="{ name: 'Badge', params: { id: scanId } }"
            class="btn-secondary text-sm !py-2 !px-4"
          >
            Badge
          </router-link>
          <button @click="shareReport" class="btn-secondary text-sm !py-2 !px-4">
            <svg class="w-4 h-4 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
            </svg>
            {{ copied ? 'Kopiert!' : 'Teilen' }}
          </button>
        </div>
      </div>
    </nav>

    <!-- Loading -->
    <div v-if="loading" class="flex-1 flex items-center justify-center">
      <div class="text-center">
        <svg class="w-8 h-8 text-blue-500 animate-spin mx-auto mb-4" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
        <p class="text-slate-400">Bericht wird geladen...</p>
      </div>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="flex-1 flex items-center justify-center px-6">
      <div class="text-center">
        <div class="w-16 h-16 rounded-full bg-red-500/10 flex items-center justify-center mx-auto mb-4">
          <svg class="w-8 h-8 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </div>
        <h2 class="text-xl font-bold mb-2">Fehler</h2>
        <p class="text-slate-400 mb-6">{{ error }}</p>
        <router-link to="/" class="btn-primary">Zurück zur Startseite</router-link>
      </div>
    </div>

    <!-- Report content -->
    <div v-else-if="scan" class="flex-1 px-6 py-10">
      <div class="max-w-4xl mx-auto">
        <!-- Header with domain -->
        <div class="text-center mb-2 animate-fade-in">
          <p class="text-sm text-slate-500 uppercase tracking-wider font-medium mb-1">Ergebnis für</p>
          <h1 class="text-2xl sm:text-3xl font-bold">{{ scan.domain }}</h1>
        </div>

        <!-- Score Circle -->
        <div class="flex justify-center my-10 animate-slide-up">
          <ScoreCircle :score="scan.score" :size="220" />
        </div>

        <!-- Category Breakdown -->
        <div class="card mb-8 animate-slide-up" style="animation-delay: 100ms">
          <h2 class="text-lg font-semibold mb-6">Kategorie-Bewertung</h2>
          <div class="space-y-5">
            <CategoryBar
              v-for="cat in categories"
              :key="cat.key"
              :name="cat.name"
              :score="cat.score"
              :max-score="cat.maxScore"
            />
          </div>
        </div>

        <!-- Top 5 Fixes -->
        <div v-if="topFixes.length > 0" class="mb-8 animate-slide-up" style="animation-delay: 200ms">
          <h2 class="text-lg font-semibold mb-4">Top Verbesserungen</h2>
          <div class="space-y-3">
            <FixCard v-for="(fix, idx) in topFixes" :key="idx" :fix="fix" />
          </div>
        </div>

        <!-- All Checks -->
        <div class="mb-8 animate-slide-up" style="animation-delay: 300ms">
          <button
            @click="showAllChecks = !showAllChecks"
            class="flex items-center gap-2 text-lg font-semibold mb-4 hover:text-blue-400 transition-colors"
          >
            Alle Checks ({{ allChecks.length }})
            <svg
              class="w-5 h-5 transition-transform duration-200"
              :class="{ 'rotate-180': showAllChecks }"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              stroke-width="2"
            >
              <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          <Transition
            enter-active-class="transition-all duration-300 ease-out"
            enter-from-class="max-h-0 opacity-0"
            enter-to-class="max-h-[2000px] opacity-100"
            leave-active-class="transition-all duration-200 ease-in"
            leave-from-class="max-h-[2000px] opacity-100"
            leave-to-class="max-h-0 opacity-0"
          >
            <div v-if="showAllChecks" class="card overflow-hidden">
              <div class="divide-y divide-slate-800/50">
                <CheckItem
                  v-for="(check, idx) in allChecks"
                  :key="idx"
                  :name="check.name"
                  :status="check.status"
                  :message="check.message"
                />
              </div>
            </div>
          </Transition>
        </div>

        <!-- CTA -->
        <div class="card text-center py-10 mb-8 animate-slide-up border-blue-500/20" style="animation-delay: 400ms">
          <div class="w-12 h-12 rounded-full bg-blue-500/10 flex items-center justify-center mx-auto mb-4">
            <svg class="w-6 h-6 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
            </svg>
          </div>
          <h3 class="text-lg font-bold mb-2">Score-Monitoring aktivieren</h3>
          <p class="text-sm text-slate-400 max-w-md mx-auto mb-6">
            Erhalte wöchentliche Updates und werde benachrichtigt, wenn sich dein Score ändert. Plus: detaillierte Analyse und Prioritäts-Empfehlungen.
          </p>
          <div class="flex flex-col sm:flex-row gap-3 justify-center">
            <button class="btn-primary">
              Pro-Version starten
            </button>
            <router-link :to="{ name: 'Badge', params: { id: scanId } }" class="btn-secondary">
              Badge herunterladen
            </router-link>
          </div>
        </div>
      </div>
    </div>

    <!-- Footer -->
    <footer class="border-t border-slate-800/50 py-6 px-6">
      <div class="max-w-4xl mx-auto flex items-center justify-between">
        <span class="text-xs text-slate-600">&copy; {{ new Date().getFullYear() }} AgentReady</span>
        <router-link to="/" class="text-xs text-slate-500 hover:text-slate-300 transition-colors">
          Neuen Scan starten
        </router-link>
      </div>
    </footer>
  </div>
</template>
