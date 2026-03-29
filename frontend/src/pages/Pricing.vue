<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { isLoggedIn } from '../auth.js'
import AppHeader from '../components/AppHeader.vue'
import { createCheckoutSession } from '../api.js'

const router = useRouter()
const purchasingFix = ref(false)
const purchasingPro = ref(false)
const error = ref('')

async function handleFixFiles() {
  if (!isLoggedIn.value) {
    router.push({ name: 'Login', query: { redirect: '/pricing' } })
    return
  }
  purchasingFix.value = true
  error.value = ''
  try {
    const session = await createCheckoutSession('fix_files', null)
    const url = session.checkout_url || session.url
    if (url) {
      window.location.href = url
    }
  } catch (e) {
    error.value = e.message || 'Could not start checkout.'
  } finally {
    purchasingFix.value = false
  }
}

async function handlePro() {
  if (!isLoggedIn.value) {
    router.push({ name: 'Login', query: { redirect: '/pricing' } })
    return
  }
  purchasingPro.value = true
  error.value = ''
  try {
    const session = await createCheckoutSession('pro', null)
    const url = session.checkout_url || session.url
    if (url) {
      window.location.href = url
    }
  } catch (e) {
    error.value = e.message || 'Could not start checkout.'
  } finally {
    purchasingPro.value = false
  }
}
</script>

<template>
  <div class="flex-1 flex flex-col">
    <!-- Nav -->
    <AppHeader />

    <!-- Hero -->
    <section class="pt-16 sm:pt-20 pb-6 px-6 lg:px-8">
      <div class="max-w-5xl mx-auto">
        <p class="text-[13px] font-display font-semibold text-accent tracking-wide uppercase mb-4">Pricing</p>
        <h1 class="font-display text-[2rem] sm:text-[2.5rem] font-bold tracking-tight leading-[1.12] text-primary max-w-lg">
          Get found by AI agents
        </h1>
        <p class="mt-4 text-[16px] text-secondary leading-relaxed max-w-[56ch]">
          Free scan tells you where you stand. Pro makes AI agents find and recommend your site.
        </p>
      </div>
    </section>

    <!-- Pricing comparison -->
    <section class="py-12 px-6 lg:px-8">
      <div class="max-w-5xl mx-auto">

        <!-- Desktop: comparison table -->
        <div class="hidden lg:block">
          <div class="border border-border rounded-lg overflow-hidden bg-surface">
            <table class="w-full text-left">
              <thead>
                <tr class="border-b border-border-light">
                  <th class="p-5 pb-4 w-[38%]">
                    <span class="text-xs text-muted font-display uppercase tracking-wider">Features</span>
                  </th>
                  <th class="p-5 pb-4 w-[20%]">
                    <div>
                      <span class="text-xs text-muted font-display uppercase tracking-wider">Free</span>
                      <p class="font-display text-2xl font-bold text-primary mt-1">$0</p>
                    </div>
                  </th>
                  <th class="p-5 pb-4 w-[22%]">
                    <div>
                      <span class="text-xs text-muted font-display uppercase tracking-wider">Fix Files</span>
                      <p class="font-display text-2xl font-bold text-primary mt-1">$9 <span class="text-sm font-normal text-secondary">one-time</span></p>
                    </div>
                  </th>
                  <th class="p-5 pb-4 w-[20%] bg-accent-light/50 relative">
                    <span class="absolute top-0 left-0 right-0 h-[3px] bg-accent rounded-b-none"></span>
                    <div>
                      <div class="flex items-center gap-2">
                        <span class="text-xs text-muted font-display uppercase tracking-wider">Pro</span>
                        <span class="text-[10px] font-display font-bold text-accent bg-accent-light px-1.5 py-0.5 rounded">Recommended</span>
                      </div>
                      <p class="font-display text-2xl font-bold text-primary mt-1">$29 <span class="text-sm font-normal text-secondary">/month</span></p>
                    </div>
                  </th>
                </tr>
              </thead>
              <tbody class="text-sm text-secondary">
                <!-- Scan + Score + Report -->
                <tr class="border-b border-border-light">
                  <td class="px-5 py-3 font-display text-primary">Scan + Score + Report</td>
                  <td class="px-5 py-3">
                    <svg class="w-4 h-4 text-score-good" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" /></svg>
                  </td>
                  <td class="px-5 py-3">
                    <svg class="w-4 h-4 text-score-good" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" /></svg>
                  </td>
                  <td class="px-5 py-3 bg-accent-light/50">
                    <svg class="w-4 h-4 text-score-good" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" /></svg>
                  </td>
                </tr>
                <!-- Generic fix suggestions -->
                <tr class="border-b border-border-light">
                  <td class="px-5 py-3 font-display text-primary">Generic fix suggestions</td>
                  <td class="px-5 py-3">
                    <svg class="w-4 h-4 text-score-good" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" /></svg>
                  </td>
                  <td class="px-5 py-3">
                    <svg class="w-4 h-4 text-score-good" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" /></svg>
                  </td>
                  <td class="px-5 py-3 bg-accent-light/50">
                    <svg class="w-4 h-4 text-score-good" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" /></svg>
                  </td>
                </tr>
                <!-- Shareable badge -->
                <tr class="border-b border-border-light">
                  <td class="px-5 py-3 font-display text-primary">Shareable badge</td>
                  <td class="px-5 py-3">
                    <svg class="w-4 h-4 text-score-good" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" /></svg>
                  </td>
                  <td class="px-5 py-3">
                    <svg class="w-4 h-4 text-score-good" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" /></svg>
                  </td>
                  <td class="px-5 py-3 bg-accent-light/50">
                    <svg class="w-4 h-4 text-score-good" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" /></svg>
                  </td>
                </tr>
                <!-- Tailored fix files -->
                <tr class="border-b border-border-light">
                  <td class="px-5 py-3">
                    <span class="font-display text-primary">Tailored fix files for your site</span>
                    <span class="block text-xs text-muted mt-0.5">ai.txt, llms.txt, robots.txt rules, UCP config</span>
                  </td>
                  <td class="px-5 py-3">
                    <svg class="w-4 h-4 text-warm-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M18 12H6" /></svg>
                  </td>
                  <td class="px-5 py-3">
                    <svg class="w-4 h-4 text-score-good" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" /></svg>
                  </td>
                  <td class="px-5 py-3 bg-accent-light/50">
                    <svg class="w-4 h-4 text-score-good" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" /></svg>
                  </td>
                </tr>
                <!-- Product & Organization Schema templates -->
                <tr class="border-b border-border-light">
                  <td class="px-5 py-3 font-display text-primary">Schema.org templates (auto-detected type)</td>
                  <td class="px-5 py-3">
                    <svg class="w-4 h-4 text-warm-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M18 12H6" /></svg>
                  </td>
                  <td class="px-5 py-3">
                    <svg class="w-4 h-4 text-score-good" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" /></svg>
                  </td>
                  <td class="px-5 py-3 bg-accent-light/50">
                    <svg class="w-4 h-4 text-score-good" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" /></svg>
                  </td>
                </tr>
                <!-- Step-by-step implementation guide -->
                <tr class="border-b border-border-light">
                  <td class="px-5 py-3 font-display text-primary">Step-by-step implementation guide</td>
                  <td class="px-5 py-3">
                    <svg class="w-4 h-4 text-warm-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M18 12H6" /></svg>
                  </td>
                  <td class="px-5 py-3">
                    <svg class="w-4 h-4 text-score-good" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" /></svg>
                  </td>
                  <td class="px-5 py-3 bg-accent-light/50">
                    <svg class="w-4 h-4 text-score-good" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" /></svg>
                  </td>
                </tr>
                <!-- ZIP download -->
                <tr class="border-b border-border-light">
                  <td class="px-5 py-3 font-display text-primary">ZIP download of all fix files</td>
                  <td class="px-5 py-3">
                    <svg class="w-4 h-4 text-warm-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M18 12H6" /></svg>
                  </td>
                  <td class="px-5 py-3">
                    <svg class="w-4 h-4 text-score-good" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" /></svg>
                  </td>
                  <td class="px-5 py-3 bg-accent-light/50">
                    <svg class="w-4 h-4 text-score-good" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" /></svg>
                  </td>
                </tr>
                <!-- Unlimited fix generation -->
                <tr class="border-b border-border-light">
                  <td class="px-5 py-3 font-display text-primary">AI agents start recommending your site</td>
                  <td class="px-5 py-3">
                    <svg class="w-4 h-4 text-warm-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M18 12H6" /></svg>
                  </td>
                  <td class="px-5 py-3">
                    <svg class="w-4 h-4 text-warm-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M18 12H6" /></svg>
                  </td>
                  <td class="px-5 py-3 bg-accent-light/50">
                    <svg class="w-4 h-4 text-score-good" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" /></svg>
                  </td>
                </tr>
                <!-- Weekly monitoring -->
                <tr class="border-b border-border-light">
                  <td class="px-5 py-3 font-display text-primary">Weekly monitoring ensures you stay visible</td>
                  <td class="px-5 py-3">
                    <svg class="w-4 h-4 text-warm-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M18 12H6" /></svg>
                  </td>
                  <td class="px-5 py-3">
                    <svg class="w-4 h-4 text-warm-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M18 12H6" /></svg>
                  </td>
                  <td class="px-5 py-3 bg-accent-light/50">
                    <svg class="w-4 h-4 text-score-good" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" /></svg>
                  </td>
                </tr>
                <!-- AI bot traffic tracking -->
                <tr class="border-b border-border-light">
                  <td class="px-5 py-3 font-display text-primary">AI Discovery Test verifies real results</td>
                  <td class="px-5 py-3">
                    <svg class="w-4 h-4 text-warm-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M18 12H6" /></svg>
                  </td>
                  <td class="px-5 py-3">
                    <svg class="w-4 h-4 text-warm-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M18 12H6" /></svg>
                  </td>
                  <td class="px-5 py-3 bg-accent-light/50">
                    <svg class="w-4 h-4 text-score-good" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" /></svg>
                  </td>
                </tr>
                <!-- Competitor comparison -->
                <tr class="border-b border-border-light">
                  <td class="px-5 py-3 font-display text-primary">Competitor comparison (up to 3)</td>
                  <td class="px-5 py-3">
                    <svg class="w-4 h-4 text-warm-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M18 12H6" /></svg>
                  </td>
                  <td class="px-5 py-3">
                    <svg class="w-4 h-4 text-warm-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M18 12H6" /></svg>
                  </td>
                  <td class="px-5 py-3 bg-accent-light/50">
                    <svg class="w-4 h-4 text-score-good" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" /></svg>
                  </td>
                </tr>
                <!-- Score history -->
                <tr class="border-b border-border-light">
                  <td class="px-5 py-3 font-display text-primary">Score history over time</td>
                  <td class="px-5 py-3">
                    <svg class="w-4 h-4 text-warm-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M18 12H6" /></svg>
                  </td>
                  <td class="px-5 py-3">
                    <svg class="w-4 h-4 text-warm-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M18 12H6" /></svg>
                  </td>
                  <td class="px-5 py-3 bg-accent-light/50">
                    <svg class="w-4 h-4 text-score-good" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" /></svg>
                  </td>
                </tr>
                <!-- Priority support -->
                <tr>
                  <td class="px-5 py-3 font-display text-primary">Priority support</td>
                  <td class="px-5 py-3">
                    <svg class="w-4 h-4 text-warm-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M18 12H6" /></svg>
                  </td>
                  <td class="px-5 py-3">
                    <svg class="w-4 h-4 text-warm-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M18 12H6" /></svg>
                  </td>
                  <td class="px-5 py-3 bg-accent-light/50">
                    <svg class="w-4 h-4 text-score-good" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" /></svg>
                  </td>
                </tr>
              </tbody>
              <!-- CTA row -->
              <tfoot>
                <tr class="border-t border-border">
                  <td class="p-5"></td>
                  <td class="p-5">
                    <router-link
                      to="/"
                      class="inline-flex items-center justify-center h-9 px-5 text-sm font-display font-semibold rounded-md border border-border text-primary hover:bg-warm-100 transition-colors"
                    >
                      Run free scan
                    </router-link>
                  </td>
                  <td class="p-5">
                    <button
                      @click="handleFixFiles"
                      :disabled="purchasingFix"
                      class="inline-flex items-center justify-center h-9 px-5 text-sm font-display font-semibold rounded-md border border-border text-primary hover:bg-warm-100 transition-colors disabled:opacity-60"
                    >
                      {{ purchasingFix ? 'Redirecting...' : (isLoggedIn ? 'Get fix files — $9' : 'Sign in to buy') }}
                    </button>
                    <p v-if="error" class="text-[11px] text-score-bad mt-1.5">{{ error }}</p>
                  </td>
                  <td class="p-5 bg-accent-light/50">
                    <button
                      @click="handlePro"
                      :disabled="purchasingPro"
                      class="inline-flex items-center justify-center h-9 px-5 text-sm font-display font-semibold rounded-md bg-accent text-white hover:bg-accent-hover transition-colors disabled:opacity-60"
                    >
                      {{ purchasingPro ? 'Redirecting...' : (isLoggedIn ? 'Start Pro — $29/mo' : 'Sign in to subscribe') }}
                    </button>
                  </td>
                </tr>
              </tfoot>
            </table>
          </div>
        </div>

        <!-- Mobile: stacked cards -->
        <div class="lg:hidden space-y-6">

          <!-- Free tier -->
          <div class="border border-border rounded-lg p-6 bg-surface">
            <div class="mb-5">
              <span class="text-xs font-display font-semibold text-muted uppercase tracking-wider">Free</span>
              <p class="font-display text-3xl font-bold text-primary mt-1">$0</p>
            </div>
            <ul class="space-y-2.5 text-sm text-secondary mb-6">
              <li class="flex items-start gap-2.5">
                <svg class="w-4 h-4 text-score-good flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" /></svg>
                Scan + Score + Report
              </li>
              <li class="flex items-start gap-2.5">
                <svg class="w-4 h-4 text-score-good flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" /></svg>
                Generic fix suggestions
              </li>
              <li class="flex items-start gap-2.5">
                <svg class="w-4 h-4 text-score-good flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" /></svg>
                Shareable badge
              </li>
            </ul>
            <router-link
              to="/"
              class="flex items-center justify-center h-10 w-full text-sm font-display font-semibold rounded-md border border-border text-primary hover:bg-warm-100 transition-colors"
            >
              Run free scan
            </router-link>
          </div>

          <!-- Fix Files tier -->
          <div class="border border-border rounded-lg p-6 bg-surface">
            <div class="mb-5">
              <span class="text-xs font-display font-semibold text-muted uppercase tracking-wider">Fix Files</span>
              <p class="font-display text-3xl font-bold text-primary mt-1">$9 <span class="text-base font-normal text-secondary">one-time</span></p>
            </div>
            <ul class="space-y-2.5 text-sm text-secondary mb-6">
              <li class="flex items-start gap-2.5">
                <svg class="w-4 h-4 text-score-good flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" /></svg>
                Everything in Free
              </li>
              <li class="flex items-start gap-2.5">
                <svg class="w-4 h-4 text-score-good flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" /></svg>
                <span>Tailored fix files <span class="text-muted">(ai.txt, llms.txt, robots.txt rules, UCP config)</span></span>
              </li>
              <li class="flex items-start gap-2.5">
                <svg class="w-4 h-4 text-score-good flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" /></svg>
                Schema.org templates (auto-detected type)
              </li>
              <li class="flex items-start gap-2.5">
                <svg class="w-4 h-4 text-score-good flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" /></svg>
                Step-by-step implementation guide
              </li>
              <li class="flex items-start gap-2.5">
                <svg class="w-4 h-4 text-score-good flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" /></svg>
                ZIP download of all fix files
              </li>
            </ul>
            <button
              @click="handleFixFiles"
              :disabled="purchasingFix"
              class="flex items-center justify-center h-10 w-full text-sm font-display font-semibold rounded-md border border-border text-primary hover:bg-warm-100 transition-colors disabled:opacity-60"
            >
              {{ purchasingFix ? 'Redirecting...' : (isLoggedIn ? 'Get fix files — $9' : 'Sign in to buy') }}
            </button>
            <p v-if="error" class="text-[11px] text-score-bad mt-2 text-center">{{ error }}</p>
          </div>

          <!-- Pro tier -->
          <div class="border-2 border-accent rounded-lg p-6 bg-surface relative">
            <span class="absolute -top-3 left-5 text-[11px] font-display font-bold text-white bg-accent px-2.5 py-0.5 rounded">Recommended</span>
            <div class="mb-5">
              <span class="text-xs font-display font-semibold text-muted uppercase tracking-wider">Pro</span>
              <p class="font-display text-3xl font-bold text-primary mt-1">$29 <span class="text-base font-normal text-secondary">/month</span></p>
            </div>
            <ul class="space-y-2.5 text-sm text-secondary mb-6">
              <li class="flex items-start gap-2.5">
                <svg class="w-4 h-4 text-score-good flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" /></svg>
                Everything in Fix Files
              </li>
              <li class="flex items-start gap-2.5">
                <svg class="w-4 h-4 text-score-good flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" /></svg>
                AI agents start recommending your site
              </li>
              <li class="flex items-start gap-2.5">
                <svg class="w-4 h-4 text-score-good flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" /></svg>
                Weekly monitoring ensures you stay visible
              </li>
              <li class="flex items-start gap-2.5">
                <svg class="w-4 h-4 text-score-good flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" /></svg>
                AI Discovery Test verifies real results
              </li>
              <li class="flex items-start gap-2.5">
                <svg class="w-4 h-4 text-score-good flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" /></svg>
                Competitor comparison (up to 3)
              </li>
              <li class="flex items-start gap-2.5">
                <svg class="w-4 h-4 text-score-good flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" /></svg>
                Score history over time
              </li>
              <li class="flex items-start gap-2.5">
                <svg class="w-4 h-4 text-score-good flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" /></svg>
                Priority support
              </li>
            </ul>
            <button
              @click="handlePro"
              :disabled="purchasingPro"
              class="flex items-center justify-center h-10 w-full text-sm font-display font-semibold rounded-md bg-accent text-white hover:bg-accent-hover transition-colors disabled:opacity-60"
            >
              {{ purchasingPro ? 'Redirecting...' : (isLoggedIn ? 'Start Pro — $29/mo' : 'Sign in to subscribe') }}
            </button>
          </div>
        </div>
      </div>
    </section>

    <!-- Note -->
    <section class="pb-20 pt-4 px-6 lg:px-8">
      <div class="max-w-5xl mx-auto">
        <p class="text-[13px] text-muted leading-relaxed text-center max-w-lg mx-auto">
          All prices in USD. Fix Files is a one-time purchase per scan. Pro is billed monthly, cancel anytime.
        </p>
      </div>
    </section>

    <!-- Footer -->
    <footer class="border-t border-border-light py-8 px-6 lg:px-8 mt-auto">
      <div class="max-w-5xl mx-auto flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <router-link to="/" class="flex items-center gap-2 text-sm text-secondary hover:text-primary transition-colors">
          <svg class="w-4 h-4 text-accent" viewBox="0 0 24 24" fill="none">
            <path d="M12 2L4 20h4l1.5-4h5L16 20h4L12 2zm0 7l2 5h-4l2-5z" fill="currentColor"/>
            <path d="M20 8a10 10 0 00-4-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" opacity="0.5"/>
            <path d="M22 6a14 14 0 00-6-5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" opacity="0.3"/>
          </svg>
          AgentCheck
        </router-link>
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
          <span>&copy; {{ new Date().getFullYear() }} AgentCheck</span>
        </div>
      </div>
    </footer>
  </div>
</template>
