<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { isLoggedIn, isPro } from '../auth.js'
import AppHeader from '../components/AppHeader.vue'
import { createCheckoutSession, createBillingPortal } from '../api.js'

const router = useRouter()
const purchasingFix = ref(false)
const purchasingPro = ref(false)
const error = ref('')
const scanUrl = ref('')

async function handleManageBilling() {
  try {
    const data = await createBillingPortal()
    const url = data.portal_url || data.url
    if (url) window.location.href = url
  } catch {
    error.value = 'Billing portal not available. Contact support to manage your subscription.'
  }
}

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

function handleScan() {
  const url = scanUrl.value.trim()
  if (!url) return
  router.push({ name: 'Home', query: { url } })
}
</script>

<template>
  <div class="flex-1 flex flex-col bg-page">
    <AppHeader />

    <!-- ─── Hero ──────────────────────────────────────────────────── -->
    <section class="pt-16 sm:pt-24 pb-10 px-6 lg:px-8">
      <div class="max-w-5xl mx-auto">
        <p class="text-[11px] font-display font-bold text-accent tracking-[0.12em] uppercase mb-5">Pricing</p>
        <h1 class="font-display text-[2.25rem] sm:text-[3rem] font-bold tracking-tight leading-[1.08] text-primary max-w-[18ch]">
          Stop losing customers<br class="hidden sm:block"> to AI
        </h1>
        <p class="mt-5 text-[16px] sm:text-[17px] text-secondary leading-relaxed max-w-[52ch]">
          Sites that optimize for AI see 3&times; more referral traffic within 90 days.
          Start free. Upgrade when results matter.
        </p>

        <!-- Current plan badge (logged-in users) -->
        <div
          v-if="isLoggedIn"
          class="mt-8 inline-flex items-center gap-3 border border-border-light rounded-lg px-4 py-2.5 bg-surface"
        >
          <span class="text-sm text-secondary font-body">Your plan:</span>
          <span
            class="inline-flex items-center px-2.5 py-1 rounded text-[11px] font-display font-bold uppercase tracking-wider"
            :class="isPro ? 'bg-accent text-white' : 'bg-warm-200 text-warm-700'"
          >
            {{ isPro ? 'Pro — $29/mo' : 'Free' }}
          </span>
          <button
            v-if="isPro"
            @click="handleManageBilling"
            class="text-xs text-accent hover:text-accent-hover transition-colors font-display font-semibold"
          >
            Manage subscription &rarr;
          </button>
        </div>
      </div>
    </section>

    <!-- ─── Pricing Cards ─────────────────────────────────────────── -->
    <section class="pb-16 px-6 lg:px-8">
      <div class="max-w-5xl mx-auto">

        <!-- Error state -->
        <p v-if="error" class="mb-6 text-[13px] text-score-bad font-body bg-red-50 border border-red-100 rounded-md px-4 py-2.5">
          {{ error }}
        </p>

        <!--
          Desktop: asymmetric 3-column grid
          Free is compact (narrower), Fix Files medium, Pro is wider + taller
          Mobile: stacked, Pro first
        -->
        <div class="flex flex-col-reverse sm:flex-col lg:grid lg:grid-cols-[220px_1fr_1fr] lg:items-start gap-4 lg:gap-5">

          <!-- ── Free (compact, understated) ───────────────────────── -->
          <div class="card-free border border-border rounded-xl p-6 bg-surface order-3 lg:order-none">
            <div class="mb-1">
              <span class="text-[10px] font-display font-bold text-muted uppercase tracking-[0.1em]">Free</span>
            </div>
            <p class="font-display text-[2rem] font-bold text-primary leading-none mt-2">$0</p>
            <p class="text-[13px] text-secondary font-body mt-3 mb-6 leading-snug">
              See where you stand
            </p>

            <ul class="space-y-2.5 mb-8">
              <li class="flex items-start gap-2.5 text-[13px] text-secondary font-body">
                <span class="check-icon flex-shrink-0 mt-0.5">
                  <svg class="w-3.5 h-3.5 text-score-good" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/>
                  </svg>
                </span>
                Scan + Score + Report
              </li>
              <li class="flex items-start gap-2.5 text-[13px] text-secondary font-body">
                <span class="check-icon flex-shrink-0 mt-0.5">
                  <svg class="w-3.5 h-3.5 text-score-good" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/>
                  </svg>
                </span>
                Generic fix suggestions
              </li>
              <li class="flex items-start gap-2.5 text-[13px] text-secondary font-body">
                <span class="check-icon flex-shrink-0 mt-0.5">
                  <svg class="w-3.5 h-3.5 text-score-good" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/>
                  </svg>
                </span>
                Shareable badge
              </li>
            </ul>

            <router-link
              to="/"
              class="flex items-center justify-center h-9 w-full text-[13px] font-display font-semibold rounded-lg border border-border text-primary hover:bg-warm-100 transition-colors"
            >
              Scan for free
            </router-link>
          </div>

          <!-- ── Fix Files ($9, medium weight) ─────────────────────── -->
          <div class="card-fix border border-border rounded-xl p-7 bg-surface order-2 lg:order-none">
            <div class="flex items-start justify-between mb-1">
              <span class="text-[10px] font-display font-bold text-muted uppercase tracking-[0.1em]">Fix Files</span>
              <span class="text-[10px] font-display font-semibold text-secondary bg-warm-100 border border-border-light px-2 py-0.5 rounded-full">One-time</span>
            </div>
            <div class="flex items-baseline gap-1.5 mt-2">
              <p class="font-display text-[2.25rem] font-bold text-primary leading-none">$9</p>
            </div>
            <p class="text-[14px] text-secondary font-body mt-3 mb-1 leading-snug font-medium">
              Get the exact files AI needs
            </p>
            <p class="text-[12px] text-muted font-body mb-6">Most popular for single sites</p>

            <ul class="space-y-3 mb-8">
              <li class="flex items-start gap-2.5 text-[13px] text-secondary font-body">
                <svg class="w-3.5 h-3.5 text-score-good flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/>
                </svg>
                Everything in Free
              </li>
              <li class="flex items-start gap-2.5 text-[13px] text-secondary font-body">
                <svg class="w-3.5 h-3.5 text-score-good flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/>
                </svg>
                <span>ai.txt, llms.txt, robots.txt rules <span class="text-muted">&amp; Schema.org templates</span></span>
              </li>
              <li class="flex items-start gap-2.5 text-[13px] text-secondary font-body">
                <svg class="w-3.5 h-3.5 text-score-good flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/>
                </svg>
                Step-by-step implementation guide
              </li>
              <li class="flex items-start gap-2.5 text-[13px] text-secondary font-body">
                <svg class="w-3.5 h-3.5 text-score-good flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/>
                </svg>
                ZIP download of all fix files
              </li>
            </ul>

            <button
              @click="handleFixFiles"
              :disabled="purchasingFix"
              class="flex items-center justify-center h-10 w-full text-[13px] font-display font-semibold rounded-lg border border-primary text-primary hover:bg-warm-100 transition-colors disabled:opacity-50"
            >
              {{ purchasingFix ? 'Redirecting...' : (isLoggedIn ? 'Get fix files — $9' : 'Sign in to buy') }}
            </button>
          </div>

          <!-- ── Pro ($29/mo, hero card) ─────────────────────────────── -->
          <div class="card-pro relative rounded-xl border-2 border-accent overflow-hidden order-1 lg:order-none" style="background: #F0F9F9;">
            <!-- Accent top bar -->
            <div class="h-1 bg-accent w-full absolute top-0 left-0"></div>

            <!-- Recommended badge -->
            <div class="absolute top-5 right-5">
              <span class="inline-flex items-center gap-1 text-[10px] font-display font-bold text-accent bg-white border border-accent/20 px-2.5 py-1 rounded-full">
                <span class="w-1.5 h-1.5 rounded-full bg-accent inline-block"></span>
                Recommended
              </span>
            </div>

            <div class="p-7 pt-8">
              <span class="text-[10px] font-display font-bold text-accent uppercase tracking-[0.1em]">Pro</span>
              <div class="flex items-baseline gap-1.5 mt-2 mb-0.5">
                <p class="font-display text-[2.5rem] font-bold text-primary leading-none">$29</p>
                <span class="text-[14px] text-secondary font-body">/month</span>
              </div>
              <p class="text-[14px] font-body font-semibold text-primary mt-3 mb-1 leading-snug">
                Get found and stay found
              </p>
              <p class="text-[12px] text-secondary font-body mb-7">Cancel anytime. No contracts.</p>

              <ul class="space-y-3 mb-8">
                <li class="flex items-start gap-2.5 text-[13px] text-secondary font-body">
                  <svg class="w-3.5 h-3.5 text-accent flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/>
                  </svg>
                  Everything in Fix Files
                </li>
                <li class="flex items-start gap-2.5 text-[13px] text-secondary font-body">
                  <svg class="w-3.5 h-3.5 text-accent flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/>
                  </svg>
                  Unlimited fix file generation
                </li>
                <li class="flex items-start gap-2.5 text-[13px] text-secondary font-body">
                  <svg class="w-3.5 h-3.5 text-accent flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/>
                  </svg>
                  Weekly monitoring + alerts
                </li>
                <li class="flex items-start gap-2.5 text-[13px] text-secondary font-body">
                  <svg class="w-3.5 h-3.5 text-accent flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/>
                  </svg>
                  <span class="text-primary font-medium">AI Discovery Test</span> &mdash; we ask ChatGPT about your business
                </li>
                <li class="flex items-start gap-2.5 text-[13px] text-secondary font-body">
                  <svg class="w-3.5 h-3.5 text-accent flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/>
                  </svg>
                  Competitor comparison
                </li>
                <li class="flex items-start gap-2.5 text-[13px] text-secondary font-body">
                  <svg class="w-3.5 h-3.5 text-accent flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/>
                  </svg>
                  Score history &amp; trend charts
                </li>
                <li class="flex items-start gap-2.5 text-[13px] text-secondary font-body">
                  <svg class="w-3.5 h-3.5 text-accent flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/>
                  </svg>
                  Content optimization suggestions
                </li>
                <li class="flex items-start gap-2.5 text-[13px] text-secondary font-body">
                  <svg class="w-3.5 h-3.5 text-accent flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/>
                  </svg>
                  Agent simulation
                </li>
              </ul>

              <button
                @click="handlePro"
                :disabled="purchasingPro"
                class="flex items-center justify-center h-11 w-full text-[14px] font-display font-bold rounded-lg bg-accent text-white hover:bg-accent-hover transition-colors disabled:opacity-50 shadow-sm"
              >
                {{ purchasingPro ? 'Redirecting...' : (isLoggedIn ? 'Start Pro — $29/mo' : 'Sign in to subscribe') }}
              </button>

              <p class="text-[11px] text-secondary font-body text-center mt-3">
                30-day money-back guarantee
              </p>
            </div>
          </div>

        </div>

        <!-- Small note -->
        <p class="mt-6 text-[12px] text-muted font-body text-center">
          All prices in USD. Fix Files is a one-time purchase per scan. Pro is billed monthly, cancel anytime.
        </p>
      </div>
    </section>

    <!-- ─── Outcomes section ──────────────────────────────────────── -->
    <section class="py-16 px-6 lg:px-8 border-t border-border-light">
      <div class="max-w-5xl mx-auto">
        <p class="text-[11px] font-display font-bold text-muted tracking-[0.12em] uppercase mb-3">What Pro users get</p>
        <h2 class="font-display text-[1.5rem] sm:text-[1.75rem] font-bold text-primary mb-10 max-w-[32ch] leading-tight">
          Real outcomes, not just features
        </h2>

        <div class="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">

          <!-- Outcome 1 -->
          <div class="outcome-card p-5 rounded-xl border border-border-light bg-surface">
            <div class="outcome-icon w-9 h-9 rounded-lg bg-accent/10 flex items-center justify-center mb-4">
              <svg class="w-4.5 h-4.5 text-accent" style="width:18px;height:18px;" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"/>
              </svg>
            </div>
            <p class="font-display font-bold text-primary text-[15px] leading-snug mb-1.5">
              2.5&times; faster score improvement
            </p>
            <p class="text-[13px] text-secondary font-body leading-relaxed">
              Pro users improve their AI readiness score faster on average than free users.
            </p>
          </div>

          <!-- Outcome 2 -->
          <div class="outcome-card p-5 rounded-xl border border-border-light bg-surface">
            <div class="outcome-icon w-9 h-9 rounded-lg bg-accent/10 flex items-center justify-center mb-4">
              <svg class="w-4.5 h-4.5 text-accent" style="width:18px;height:18px;" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/>
              </svg>
            </div>
            <p class="font-display font-bold text-primary text-[15px] leading-snug mb-1.5">
              AI Discovery Test
            </p>
            <p class="text-[13px] text-secondary font-body leading-relaxed">
              We actually ask ChatGPT about your business and show you exactly what it says.
            </p>
          </div>

          <!-- Outcome 3 -->
          <div class="outcome-card p-5 rounded-xl border border-border-light bg-surface">
            <div class="outcome-icon w-9 h-9 rounded-lg bg-accent/10 flex items-center justify-center mb-4">
              <svg class="w-4.5 h-4.5 text-accent" style="width:18px;height:18px;" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"/>
              </svg>
            </div>
            <p class="font-display font-bold text-primary text-[15px] leading-snug mb-1.5">
              Catch issues early
            </p>
            <p class="text-[13px] text-secondary font-body leading-relaxed">
              Weekly alerts surface ranking drops before they cost you traffic.
            </p>
          </div>

          <!-- Outcome 4 -->
          <div class="outcome-card p-5 rounded-xl border border-border-light bg-surface">
            <div class="outcome-icon w-9 h-9 rounded-lg bg-accent/10 flex items-center justify-center mb-4">
              <svg class="w-4.5 h-4.5 text-accent" style="width:18px;height:18px;" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
              </svg>
            </div>
            <p class="font-display font-bold text-primary text-[15px] leading-snug mb-1.5">
              Beat your competitors
            </p>
            <p class="text-[13px] text-secondary font-body leading-relaxed">
              Compare your score against up to 3 competitors to see exactly where to focus.
            </p>
          </div>

        </div>
      </div>
    </section>

    <!-- ─── ROI Section ───────────────────────────────────────────── -->
    <section class="py-16 px-6 lg:px-8 border-t border-border-light">
      <div class="max-w-5xl mx-auto">
        <p class="text-[11px] font-display font-bold text-muted tracking-[0.12em] uppercase mb-3">The math</p>
        <h2 class="font-display text-[1.5rem] sm:text-[1.75rem] font-bold text-primary mb-2 leading-tight">
          What does one extra customer cost?
        </h2>
        <p class="text-[15px] text-secondary font-body mb-12 max-w-[52ch]">
          If AI sends you just 10 extra customers per month at a $50 average order value&hellip;
        </p>

        <div class="roi-grid grid sm:grid-cols-3 gap-px bg-border-light rounded-xl overflow-hidden border border-border-light">

          <!-- Cell 1 -->
          <div class="roi-cell bg-surface px-7 py-8 flex flex-col">
            <p class="text-[12px] font-display font-semibold text-muted uppercase tracking-wider mb-3">Customers from AI</p>
            <p class="roi-number font-display font-bold text-primary leading-none">
              10 <span class="text-[1rem] font-normal text-secondary">/mo</span>
            </p>
            <p class="text-[13px] text-muted font-body mt-3">Realistic estimate for an optimized site</p>
          </div>

          <!-- Cell 2 -->
          <div class="roi-cell bg-surface px-7 py-8 flex flex-col">
            <p class="text-[12px] font-display font-semibold text-muted uppercase tracking-wider mb-3">Revenue generated</p>
            <p class="roi-number font-display font-bold text-score-good leading-none">
              $500 <span class="text-[1rem] font-normal text-secondary">/mo</span>
            </p>
            <p class="text-[13px] text-muted font-body mt-3">At $50 average order value</p>
          </div>

          <!-- Cell 3 -->
          <div class="roi-cell bg-surface px-7 py-8 flex flex-col">
            <p class="text-[12px] font-display font-semibold text-muted uppercase tracking-wider mb-3">Your Pro investment</p>
            <p class="roi-number font-display font-bold text-primary leading-none">
              $29 <span class="text-[1rem] font-normal text-secondary">/mo</span>
            </p>
            <p class="text-[13px] text-muted font-body mt-3">That&rsquo;s a <strong class="text-accent font-bold">17&times; return</strong> on Pro</p>
          </div>

        </div>

        <!-- Equation callout -->
        <div class="mt-6 flex flex-wrap items-center gap-2 text-[14px] font-body text-secondary">
          <span class="font-display font-semibold text-primary">10 customers</span>
          <span class="text-muted">&times;</span>
          <span class="font-display font-semibold text-primary">$50 avg order</span>
          <span class="text-muted">=</span>
          <span class="font-display font-bold text-score-good text-[16px]">$500/mo value</span>
          <span class="text-muted mx-1">vs.</span>
          <span class="font-display font-bold text-primary">$29/mo Pro</span>
        </div>
      </div>
    </section>

    <!-- ─── FAQ ───────────────────────────────────────────────────── -->
    <section class="py-16 px-6 lg:px-8 border-t border-border-light">
      <div class="max-w-5xl mx-auto">
        <div class="grid lg:grid-cols-[280px_1fr] gap-12">

          <div>
            <p class="text-[11px] font-display font-bold text-muted tracking-[0.12em] uppercase mb-3">FAQ</p>
            <h2 class="font-display text-[1.5rem] font-bold text-primary leading-tight">
              Common questions
            </h2>
          </div>

          <div class="space-y-0 divide-y divide-border-light">

            <details class="faq-item group py-5 cursor-pointer list-none" open>
              <summary class="flex items-center justify-between gap-4 font-display font-semibold text-[14px] text-primary select-none list-none">
                Can I cancel anytime?
                <svg class="w-4 h-4 text-muted flex-shrink-0 transition-transform group-open:rotate-180" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7"/>
                </svg>
              </summary>
              <p class="mt-3 text-[13px] text-secondary font-body leading-relaxed">
                Yes. Pro is month-to-month with no contracts. Cancel in one click from your billing portal and you won&rsquo;t be charged again.
              </p>
            </details>

            <details class="faq-item group py-5 cursor-pointer">
              <summary class="flex items-center justify-between gap-4 font-display font-semibold text-[14px] text-primary select-none list-none">
                What if I only have one site?
                <svg class="w-4 h-4 text-muted flex-shrink-0 transition-transform group-open:rotate-180" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7"/>
                </svg>
              </summary>
              <p class="mt-3 text-[13px] text-secondary font-body leading-relaxed">
                Fix Files is perfect. One scan, one purchase, all the files you need. You can always upgrade to Pro later if you want ongoing monitoring.
              </p>
            </details>

            <details class="faq-item group py-5 cursor-pointer">
              <summary class="flex items-center justify-between gap-4 font-display font-semibold text-[14px] text-primary select-none list-none">
                Do you offer annual pricing?
                <svg class="w-4 h-4 text-muted flex-shrink-0 transition-transform group-open:rotate-180" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7"/>
                </svg>
              </summary>
              <p class="mt-3 text-[13px] text-secondary font-body leading-relaxed">
                Annual billing is coming soon with a discount. Sign up for Pro now and we&rsquo;ll offer you the annual option when it launches.
              </p>
            </details>

            <details class="faq-item group py-5 cursor-pointer">
              <summary class="flex items-center justify-between gap-4 font-display font-semibold text-[14px] text-primary select-none list-none">
                What payment methods do you accept?
                <svg class="w-4 h-4 text-muted flex-shrink-0 transition-transform group-open:rotate-180" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7"/>
                </svg>
              </summary>
              <p class="mt-3 text-[13px] text-secondary font-body leading-relaxed">
                We use Stripe for payments. All major credit and debit cards are accepted (Visa, Mastercard, Amex). Your payment info is never stored on our servers.
              </p>
            </details>

            <details class="faq-item group py-5 cursor-pointer">
              <summary class="flex items-center justify-between gap-4 font-display font-semibold text-[14px] text-primary select-none list-none">
                How does the AI Discovery Test work?
                <svg class="w-4 h-4 text-muted flex-shrink-0 transition-transform group-open:rotate-180" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7"/>
                </svg>
              </summary>
              <p class="mt-3 text-[13px] text-secondary font-body leading-relaxed">
                We send queries about your business category to AI assistants like ChatGPT and record whether your site appears in the responses. You see the raw answers, not just a score.
              </p>
            </details>

          </div>
        </div>
      </div>
    </section>

    <!-- ─── Bottom CTA ────────────────────────────────────────────── -->
    <section class="py-16 px-6 lg:px-8 border-t border-border-light">
      <div class="max-w-5xl mx-auto text-center">
        <h2 class="font-display text-[1.75rem] sm:text-[2rem] font-bold text-primary mb-3 leading-tight">
          Start with a free scan.<br class="hidden sm:block"> Upgrade when you&rsquo;re ready.
        </h2>
        <p class="text-[15px] text-secondary font-body mb-8 max-w-[44ch] mx-auto">
          No credit card required. See your AI readiness score in under 60 seconds.
        </p>

        <!-- Scan input -->
        <form
          @submit.prevent="handleScan"
          class="flex flex-col sm:flex-row items-stretch sm:items-center gap-2.5 max-w-[480px] mx-auto"
        >
          <input
            v-model="scanUrl"
            type="url"
            placeholder="https://yourdomain.com"
            class="flex-1 h-11 px-4 rounded-lg border border-border bg-surface text-[14px] font-body text-primary placeholder:text-muted focus:outline-none focus:ring-2 focus:ring-accent/30 focus:border-accent transition-colors"
          />
          <button
            type="submit"
            class="h-11 px-6 rounded-lg bg-accent text-white font-display font-bold text-[14px] hover:bg-accent-hover transition-colors whitespace-nowrap"
          >
            Scan for free
          </button>
        </form>

        <p class="mt-4 text-[12px] text-muted font-body">
          Or <router-link to="/" class="text-accent hover:text-accent-hover transition-colors">go to the home page</router-link> to scan without an account.
        </p>
      </div>
    </section>

    <!-- ─── Footer ────────────────────────────────────────────────── -->
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
            href="https://github.com/lennystepn-hue/agentcheck"
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

<style scoped>
/* Card entrance animation */
.card-free,
.card-fix,
.card-pro {
  animation: card-rise 0.4s cubic-bezier(0.16, 1, 0.3, 1) both;
}
.card-fix { animation-delay: 0.06s; }
.card-pro { animation-delay: 0.12s; }

@keyframes card-rise {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Outcome card hover */
.outcome-card {
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}
.outcome-card:hover {
  border-color: #C5DEDE;
  box-shadow: 0 2px 12px rgba(13, 115, 119, 0.07);
}

/* ROI numbers — count-up shimmer on load */
.roi-number {
  font-size: clamp(2rem, 4vw, 2.75rem);
  animation: roi-reveal 0.7s cubic-bezier(0.16, 1, 0.3, 1) both;
}
.roi-cell:nth-child(2) .roi-number { animation-delay: 0.15s; }
.roi-cell:nth-child(3) .roi-number { animation-delay: 0.3s; }

@keyframes roi-reveal {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* FAQ details marker removal cross-browser */
details > summary::-webkit-details-marker { display: none; }
details > summary { list-style: none; }

/* Pro card subtle glow on hover */
.card-pro {
  transition: box-shadow 0.25s ease;
}
.card-pro:hover {
  box-shadow: 0 8px 32px rgba(13, 115, 119, 0.12);
}
</style>
