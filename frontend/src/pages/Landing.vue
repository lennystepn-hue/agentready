<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { startScan } from '../api.js'

const router = useRouter()
const domain = ref('')
const loading = ref(false)
const error = ref('')

async function handleScan() {
  const value = domain.value.trim()
  if (!value) return

  error.value = ''
  loading.value = true

  try {
    const result = await startScan(value)
    router.push({ name: 'ScanProgress', params: { id: result.scan_id } })
  } catch (e) {
    error.value = e.message || 'Scan konnte nicht gestartet werden.'
  } finally {
    loading.value = false
  }
}

const features = [
  {
    icon: 'protocol',
    title: 'Protokoll-Erkennung',
    description: 'Prüft ob dein Shop via MCP, llms.txt oder AI-Plugin erreichbar ist.',
  },
  {
    icon: 'data',
    title: 'Strukturierte Daten',
    description: 'Analysiert Schema.org Markup, Open Graph und Produkt-Feeds für Agents.',
  },
  {
    icon: 'trust',
    title: 'Trust & Sicherheit',
    description: 'Bewertet HTTPS, Datenschutz-Signale und Rückgabe-Richtlinien für automatisierte Käufe.',
  },
]
</script>

<template>
  <div class="flex-1">
    <!-- Nav -->
    <nav class="border-b border-slate-800/50">
      <div class="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
        <div class="flex items-center gap-2">
          <div class="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center">
            <svg class="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <span class="font-bold text-lg">AgentReady</span>
        </div>
        <a href="#warum" class="text-sm text-slate-400 hover:text-slate-200 transition-colors">
          Warum Agent Readiness?
        </a>
      </div>
    </nav>

    <!-- Hero -->
    <section class="pt-24 pb-20 px-6">
      <div class="max-w-3xl mx-auto text-center">
        <div class="animate-fade-in">
          <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-xs font-medium mb-8">
            <span class="relative flex h-2 w-2">
              <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
              <span class="relative inline-flex rounded-full h-2 w-2 bg-blue-500"></span>
            </span>
            Open Beta
          </div>
        </div>

        <h1 class="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight leading-tight animate-slide-up">
          Wie findbar ist dein Shop
          <br />
          <span class="text-gradient">für AI Agents?</span>
        </h1>

        <p class="mt-6 text-lg text-slate-400 max-w-xl mx-auto animate-slide-up" style="animation-delay: 100ms">
          Scanne deine Website und erfahre, wie gut AI-Agenten deine Produkte finden, verstehen und kaufen können.
        </p>

        <!-- Scan Input -->
        <form
          @submit.prevent="handleScan"
          class="mt-10 flex flex-col sm:flex-row gap-3 max-w-xl mx-auto animate-slide-up"
          style="animation-delay: 200ms"
        >
          <div class="relative flex-1">
            <div class="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
              <svg class="w-4 h-4 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10" />
                <path d="M2 12h20M12 2a15.3 15.3 0 014 10 15.3 15.3 0 01-4 10 15.3 15.3 0 01-4-10 15.3 15.3 0 014-10z" />
              </svg>
            </div>
            <input
              v-model="domain"
              type="text"
              placeholder="dein-shop.de"
              class="input-field pl-10"
              :disabled="loading"
            />
          </div>
          <button
            type="submit"
            class="btn-primary whitespace-nowrap"
            :disabled="loading || !domain.trim()"
          >
            <svg v-if="loading" class="w-4 h-4 mr-2 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            {{ loading ? 'Wird gestartet...' : 'Scannen' }}
          </button>
        </form>

        <p v-if="error" class="mt-3 text-sm text-red-400">{{ error }}</p>

        <p class="mt-4 text-xs text-slate-600 animate-slide-up" style="animation-delay: 300ms">
          Kostenlos &middot; Keine Registrierung &middot; Ergebnis in unter 30 Sekunden
        </p>
      </div>
    </section>

    <!-- Why section -->
    <section id="warum" class="py-20 px-6 border-t border-slate-800/50">
      <div class="max-w-5xl mx-auto">
        <h2 class="text-2xl sm:text-3xl font-bold text-center mb-4">
          Warum Agent Readiness?
        </h2>
        <p class="text-slate-400 text-center max-w-2xl mx-auto mb-12">
          AI-Agenten werden zur neuen Suchmaschine. Wer nicht maschinenlesbar ist, wird unsichtbar.
        </p>

        <!-- Feature cards -->
        <div class="grid sm:grid-cols-3 gap-6">
          <div
            v-for="feature in features"
            :key="feature.title"
            class="card group hover:border-slate-700 transition-all duration-200"
          >
            <div class="w-10 h-10 rounded-lg bg-blue-500/10 flex items-center justify-center mb-4">
              <!-- Protocol icon -->
              <svg v-if="feature.icon === 'protocol'" class="w-5 h-5 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M7.5 21L3 16.5m0 0L7.5 12M3 16.5h13.5m0-13.5L21 7.5m0 0L16.5 12M21 7.5H7.5" />
              </svg>
              <!-- Data icon -->
              <svg v-if="feature.icon === 'data'" class="w-5 h-5 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M17.25 6.75L22.5 12l-5.25 5.25m-10.5 0L1.5 12l5.25-5.25m7.5-3l-4.5 16.5" />
              </svg>
              <!-- Trust icon -->
              <svg v-if="feature.icon === 'trust'" class="w-5 h-5 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
              </svg>
            </div>
            <h3 class="font-semibold text-slate-200 mb-2">{{ feature.title }}</h3>
            <p class="text-sm text-slate-400 leading-relaxed">{{ feature.description }}</p>
          </div>
        </div>

        <!-- Quote -->
        <div class="mt-16 text-center">
          <blockquote class="relative max-w-2xl mx-auto">
            <svg class="absolute -top-4 -left-4 w-8 h-8 text-slate-800" fill="currentColor" viewBox="0 0 24 24">
              <path d="M14.017 21v-7.391c0-5.704 3.731-9.57 8.983-10.609l.995 2.151c-2.432.917-3.995 3.638-3.995 5.849h4v10H14.017zm-14.017 0v-7.391c0-5.704 3.731-9.57 8.983-10.609l.995 2.151c-2.432.917-3.995 3.638-3.995 5.849h4v10H0z" />
            </svg>
            <p class="text-lg sm:text-xl font-medium text-slate-300 italic leading-relaxed">
              &bdquo;AI Agents werden 2026 für $20.9 Mrd an Retail-Ausgaben verantwortlich sein.&ldquo;
            </p>
            <footer class="mt-3 text-sm text-slate-500">
              — Gartner Research, 2025
            </footer>
          </blockquote>
        </div>
      </div>
    </section>

    <!-- Footer -->
    <footer class="border-t border-slate-800/50 py-8 px-6">
      <div class="max-w-5xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
        <div class="flex items-center gap-2 text-slate-500 text-sm">
          <div class="w-5 h-5 bg-blue-500 rounded flex items-center justify-center">
            <svg class="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
              <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
            </svg>
          </div>
          AgentReady
        </div>
        <p class="text-xs text-slate-600">
          &copy; {{ new Date().getFullYear() }} AgentReady. Alle Rechte vorbehalten.
        </p>
      </div>
    </footer>
  </div>
</template>
