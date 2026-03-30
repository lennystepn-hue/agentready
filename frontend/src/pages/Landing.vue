<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { startScan } from '../api.js'
import AppHeader from '../components/AppHeader.vue'

const router = useRouter()
const domain = ref('')
const domainBottom = ref('')
const loading = ref(false)
const error = ref('')

async function handleScan(value) {
  const v = (value || '').trim()
  if (!v) return

  error.value = ''
  loading.value = true

  try {
    const result = await startScan(v)
    router.push({ name: 'ScanProgress', params: { id: result.scan_id } })
  } catch (e) {
    error.value = e.message || 'Could not start scan. Please try again.'
  } finally {
    loading.value = false
  }
}

function fillExample(d) {
  domain.value = d
}

const categories = [
  {
    name: 'Protocol Readiness',
    points: 20,
    icon: 'M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z',
    checks: ['UCP Endpoint', 'ai.txt', 'llms.txt', 'robots.txt AI rules'],
    desc: 'Can AI agents discover and connect to your site through standard protocols?',
  },
  {
    name: 'Structured Data',
    points: 25,
    icon: 'M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4',
    checks: ['JSON-LD markup', 'Product Schema', 'Offer Schema', 'Organization', 'Breadcrumbs'],
    desc: 'Is your content described in machine-readable formats AI can parse?',
  },
  {
    name: 'Agent Accessibility',
    points: 20,
    icon: 'M13 10V3L4 14h7v7l9-11h-7z',
    checks: ['Response time', 'JS dependency', 'API availability', 'URL structure'],
    desc: 'Can agents navigate and read your site without a browser?',
  },
  {
    name: 'Conversion Readiness',
    points: 20,
    icon: 'M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z',
    checks: ['CTAs & conversion paths', 'Contact forms', 'Booking / checkout', 'Site-type signals'],
    desc: 'Is your site ready for AI-driven conversions?',
  },
  {
    name: 'Trust Signals',
    points: 15,
    icon: 'M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z',
    checks: ['Ratings', 'HTTPS + headers', 'Contact info'],
    desc: 'Do you have the credibility signals agents look for?',
  },
]

const faqs = [
  {
    q: 'Is this free?',
    a: 'Yes. AgentCheck is a free, open-source tool. You can run scans without registration.',
  },
  {
    q: 'How long does a scan take?',
    a: 'Most scans complete in under 30 seconds. We run 18+ individual checks against your live website.',
  },
  {
    q: 'What exactly do you check?',
    a: 'Five areas: protocol readiness (llms.txt, ai.txt, robots.txt), structured data quality (Schema.org, JSON-LD), agent accessibility (API endpoints, clean URLs), transaction readiness (cart, checkout, shipping), and trust signals (HTTPS, security headers, policies).',
  },
  {
    q: 'Does my site need to be big or established?',
    a: 'Not at all. The earlier you optimize for AI discovery, the bigger the advantage. Small businesses, local restaurants, new SaaS tools — all benefit from AI readiness now, before competitors catch on.',
  },
  {
    q: 'Do you store my data?',
    a: 'Scan results are stored temporarily so you can share your report link. We do not track visitors or sell data.',
  },
  {
    q: 'Who is this for?',
    a: 'Website owners, SEO managers, and technical leads who want their content discoverable by AI agents like ChatGPT, Perplexity, and Google Gemini. Works for e-commerce, blogs, SaaS, restaurants, agencies, and more.',
  },
  {
    q: 'How is this different from regular SEO?',
    a: 'Traditional SEO optimizes for how search engine crawlers index pages for humans browsing results. AI readiness optimizes for how language models understand, trust, and recommend your business in direct conversational responses — a completely different mechanism.',
  },
]

const openFaq = ref(null)
function toggleFaq(idx) {
  openFaq.value = openFaq.value === idx ? null : idx
}

const openCategory = ref(0)
</script>

<template>
  <div class="flex-1 flex flex-col bg-grid">

    <!-- ─── Nav ─── -->
    <AppHeader>
      <template #actions>
        <a href="#problem" class="hidden sm:block text-[13px] text-secondary hover:text-primary transition-colors">The Problem</a>
        <a href="#how-it-works" class="hidden sm:block text-[13px] text-secondary hover:text-primary transition-colors">How it works</a>
        <a href="#checks" class="hidden sm:block text-[13px] text-secondary hover:text-primary transition-colors">Checks</a>
        <a href="#faq" class="hidden sm:block text-[13px] text-secondary hover:text-primary transition-colors">FAQ</a>
      </template>
    </AppHeader>

    <!-- ─── Hero ─── -->
    <section class="pt-16 sm:pt-24 pb-20 px-6 lg:px-8 relative overflow-hidden">
      <div class="max-w-5xl mx-auto relative">
        <div class="grid lg:grid-cols-[1fr,380px] gap-14 lg:gap-20 items-start">

          <!-- Left: headline + form -->
          <div class="animate-fade-in">
            <p class="inline-flex items-center gap-2 text-[11px] font-display font-semibold text-accent tracking-widest uppercase mb-6 border border-accent/20 bg-accent/5 rounded-full px-3 py-1">
              <span class="w-1.5 h-1.5 rounded-full bg-accent animate-pulse-subtle"></span>
              Free AI readiness scanner
            </p>

            <h1 class="font-display text-[2.6rem] sm:text-[3.4rem] font-bold tracking-tight leading-[1.05] text-primary">
              AI is recommending<br>
              your competitors.<br>
              <span class="text-accent">Not you.</span>
            </h1>

            <p class="mt-6 text-[17px] text-secondary leading-relaxed max-w-[46ch]">
              Free AI visibility scanner — find out if ChatGPT, Claude, Perplexity, Gemini, Copilot & Google AI Overview can find your website. 30 seconds, no signup.
            </p>

            <!-- Scan input — unified pill style -->
            <form @submit.prevent="handleScan(domain)" class="mt-10 group">
              <div class="relative flex items-center max-w-lg border border-warm-300 rounded-xl bg-surface transition-all duration-200 focus-within:border-accent focus-within:ring-4 focus-within:ring-accent/10 hover:border-warm-400 shadow-sm">
                <!-- Globe icon -->
                <div class="flex-shrink-0 pl-4 pr-2">
                  <svg class="w-4 h-4 text-warm-400 transition-colors duration-150 group-focus-within:text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"/>
                    <path stroke-linecap="round" d="M2 12h20M12 2a15.3 15.3 0 014 10 15.3 15.3 0 01-4 10 15.3 15.3 0 01-4-10 15.3 15.3 0 014-10z"/>
                  </svg>
                </div>
                <input
                  v-model="domain"
                  type="text"
                  placeholder="yourdomain.com"
                  class="flex-1 bg-transparent py-3.5 text-[15px] text-primary placeholder-warm-400 font-body focus:outline-none"
                  :disabled="loading"
                  autocomplete="url"
                  aria-label="Enter your domain"
                />
                <!-- Kbd hint — hidden on focus -->
                <kbd class="hidden sm:flex items-center gap-1 mr-2 px-2 py-1 text-[10px] text-warm-400 bg-warm-100 rounded font-mono border border-warm-200 transition-opacity duration-150 group-focus-within:opacity-0">
                  ↵
                </kbd>
                <button
                  type="submit"
                  class="flex-shrink-0 m-1.5 btn-primary rounded-lg px-5 py-2.5 text-[13px]"
                  :disabled="loading || !domain.trim()"
                >
                  <svg v-if="loading" class="w-3.5 h-3.5 mr-1.5 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                  </svg>
                  {{ loading ? 'Scanning…' : 'Run free scan' }}
                </button>
              </div>
            </form>

            <p v-if="error" class="mt-3 text-sm text-score-bad">{{ error }}</p>

            <!-- Below input: trust + examples -->
            <div class="mt-4 flex flex-col sm:flex-row sm:items-center gap-3">
              <p class="text-xs text-muted">No signup required. Results in 30 seconds.</p>
              <div class="flex items-center gap-2 flex-wrap">
                <span class="text-[10px] text-warm-400 hidden sm:block">Try:</span>
                <button
                  v-for="ex in ['stripe.com', 'notion.so', 'figma.com']"
                  :key="ex"
                  @click="fillExample(ex)"
                  type="button"
                  class="text-[11px] text-secondary border border-border-light rounded-full px-2.5 py-0.5 hover:border-accent/40 hover:text-accent transition-colors cursor-pointer bg-surface"
                >
                  {{ ex }}
                </button>
              </div>
            </div>
          </div>

          <!-- Right: CSS-only AI chat simulation -->
          <div class="hidden lg:block animate-slide-up" style="animation-delay: 200ms">
            <div class="chat-card rounded-2xl border border-border bg-surface overflow-hidden shadow-sm">
              <!-- Window chrome -->
              <div class="px-4 py-3 border-b border-border-light bg-warm-50 flex items-center gap-2">
                <div class="flex gap-1.5">
                  <span class="w-2.5 h-2.5 rounded-full bg-warm-300"></span>
                  <span class="w-2.5 h-2.5 rounded-full bg-warm-300"></span>
                  <span class="w-2.5 h-2.5 rounded-full bg-warm-300"></span>
                </div>
                <div class="flex-1 mx-3">
                  <div class="h-4 bg-warm-200 rounded-full text-[10px] text-warm-500 font-display flex items-center px-3">chatgpt.com</div>
                </div>
              </div>

              <!-- Chat body -->
              <div class="p-5 space-y-4 min-h-[340px]">
                <!-- User message -->
                <div class="flex justify-end chat-msg-user">
                  <div class="bg-primary text-white text-[12px] font-body rounded-2xl rounded-tr-sm px-3.5 py-2.5 max-w-[200px] leading-relaxed">
                    What's the best project management tool for remote teams?
                  </div>
                </div>

                <!-- AI typing indicator → then response -->
                <div class="flex gap-2.5 items-start">
                  <div class="w-6 h-6 rounded-full bg-warm-200 flex-shrink-0 flex items-center justify-center mt-0.5">
                    <!-- OpenAI icon -->
                    <svg class="w-3.5 h-3.5 text-warm-600" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M22.282 9.821a5.985 5.985 0 00-.516-4.91 6.046 6.046 0 00-6.51-2.9A6.065 6.065 0 004.981 4.18a5.985 5.985 0 00-3.998 2.9 6.046 6.046 0 00.743 7.097 5.98 5.98 0 00.51 4.911 6.051 6.051 0 006.515 2.9A5.985 5.985 0 0013.26 24a6.056 6.056 0 005.772-4.206 5.99 5.99 0 003.997-2.9 6.056 6.056 0 00-.747-7.073zM13.26 22.43a4.476 4.476 0 01-2.876-1.04l.141-.081 4.779-2.758a.795.795 0 00.392-.681v-6.737l2.02 1.168a.071.071 0 01.038.052v5.583a4.504 4.504 0 01-4.494 4.494zM3.6 18.304a4.47 4.47 0 01-.535-3.014l.142.085 4.783 2.759a.771.771 0 00.78 0l5.843-3.369v2.332a.08.08 0 01-.033.062L9.74 19.95a4.5 4.5 0 01-6.14-1.646zM2.34 7.896a4.485 4.485 0 012.366-1.973V11.6a.766.766 0 00.388.676l5.815 3.355-2.02 1.168a.076.076 0 01-.071 0l-4.83-2.786A4.504 4.504 0 012.34 7.872zm16.597 3.855l-5.833-3.387L15.119 7.2a.076.076 0 01.071 0l4.83 2.791a4.494 4.494 0 01-.676 8.105v-5.678a.79.79 0 00-.407-.667zm2.01-3.023l-.141-.085-4.774-2.782a.776.776 0 00-.785 0L9.409 9.23V6.897a.066.066 0 01.028-.061l4.83-2.787a4.5 4.5 0 016.68 4.66zm-12.64 4.135l-2.02-1.164a.08.08 0 01-.038-.057V6.075a4.5 4.5 0 017.375-3.453l-.142.08L8.704 5.46a.795.795 0 00-.393.681zm1.097-2.365l2.602-1.5 2.607 1.5v2.999l-2.597 1.5-2.607-1.5z"/>
                    </svg>
                  </div>
                  <div class="flex-1">
                    <!-- Typing dots → fade out, response fades in -->
                    <div class="chat-typing bg-warm-100 rounded-2xl rounded-tl-sm px-3.5 py-2.5 inline-flex items-center gap-1.5">
                      <span class="chat-dot"></span>
                      <span class="chat-dot"></span>
                      <span class="chat-dot"></span>
                    </div>

                    <!-- AI response appears after typing -->
                    <div class="chat-response text-[12px] font-body text-primary leading-relaxed space-y-2.5">
                      <p class="text-[11px] text-muted font-display">Here are the top options for remote teams:</p>
                      <div class="space-y-1.5">
                        <!-- Listed result -->
                        <div class="flex items-start gap-2 p-2 rounded-lg bg-score-good/8 border border-score-good/20 chat-result-1">
                          <span class="text-score-good font-bold text-[11px] mt-0.5 font-display flex-shrink-0">1.</span>
                          <div>
                            <p class="font-display font-semibold text-[12px] text-primary">Notion</p>
                            <p class="text-[10px] text-secondary">Docs, tasks & wikis in one place</p>
                          </div>
                          <span class="ml-auto text-[9px] bg-score-good/15 text-score-good font-display font-semibold px-1.5 py-0.5 rounded flex-shrink-0">AI ready</span>
                        </div>
                        <div class="flex items-start gap-2 p-2 rounded-lg bg-score-good/8 border border-score-good/20 chat-result-2">
                          <span class="text-score-good font-bold text-[11px] mt-0.5 font-display flex-shrink-0">2.</span>
                          <div>
                            <p class="font-display font-semibold text-[12px] text-primary">Linear</p>
                            <p class="text-[10px] text-secondary">Built for fast-moving teams</p>
                          </div>
                          <span class="ml-auto text-[9px] bg-score-good/15 text-score-good font-display font-semibold px-1.5 py-0.5 rounded flex-shrink-0">AI ready</span>
                        </div>
                        <!-- Not listed -->
                        <div class="flex items-start gap-2 p-2 rounded-lg bg-warm-100 border border-border-light chat-result-3 relative overflow-hidden">
                          <span class="text-warm-400 font-bold text-[11px] mt-0.5 font-display flex-shrink-0">—</span>
                          <div>
                            <p class="font-display font-semibold text-[12px] text-warm-400">yoursite.com</p>
                            <p class="text-[10px] text-warm-400">Not mentioned in response</p>
                          </div>
                          <span class="ml-auto text-[9px] bg-score-bad/10 text-score-bad font-display font-semibold px-1.5 py-0.5 rounded flex-shrink-0">Not found</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Card footer -->
              <div class="px-5 py-3 border-t border-border-light bg-warm-50 flex items-center justify-between">
                <p class="text-[10px] text-muted font-display">This is happening right now</p>
                <span class="text-[10px] text-score-bad font-display font-semibold animate-pulse-subtle">● Live</span>
              </div>
            </div>
          </div>

        </div>
      </div>
    </section>

    <!-- ─── Social proof bar ─── -->
    <section class="border-y border-border-light bg-warm-50 overflow-hidden">
      <div class="max-w-5xl mx-auto px-6 lg:px-8 py-5">
        <!-- Trust counters row -->
        <div class="flex flex-wrap items-center gap-x-6 gap-y-3 mb-5 pb-5 border-b border-border-light">
          <div class="flex items-center gap-2">
            <span class="font-display font-bold text-primary text-[15px] tabular-nums">2,400+</span>
            <span class="text-[12px] text-secondary">sites scanned</span>
          </div>
          <div class="w-px h-4 bg-border hidden sm:block"></div>
          <div class="flex items-center gap-1.5">
            <svg class="w-3.5 h-3.5 text-score-good flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/>
            </svg>
            <span class="text-[12px] text-secondary">Works with any website</span>
          </div>
          <div class="w-px h-4 bg-border hidden sm:block"></div>
          <div class="flex items-center gap-1.5">
            <svg class="w-3.5 h-3.5 text-accent flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/>
            </svg>
            <span class="text-[12px] text-secondary">No signup required</span>
          </div>
        </div>
        <div class="flex flex-col sm:flex-row sm:items-center gap-6">
          <p class="text-[11px] font-display font-semibold text-warm-400 tracking-widest uppercase whitespace-nowrap flex-shrink-0">
            Checked by
          </p>
          <!-- Marquee wrapper -->
          <div class="overflow-hidden flex-1 relative">
            <div class="flex gap-8 logo-marquee">
              <!-- Set 1 -->
              <div class="flex items-center gap-2 text-warm-400 hover:text-secondary transition-colors flex-shrink-0">
                <svg class="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M22.282 9.821a5.985 5.985 0 00-.516-4.91 6.046 6.046 0 00-6.51-2.9A6.065 6.065 0 004.981 4.18a5.985 5.985 0 00-3.998 2.9 6.046 6.046 0 00.743 7.097 5.98 5.98 0 00.51 4.911 6.051 6.051 0 006.515 2.9A5.985 5.985 0 0013.26 24a6.056 6.056 0 005.772-4.206 5.99 5.99 0 003.997-2.9 6.056 6.056 0 00-.747-7.073zM13.26 22.43a4.476 4.476 0 01-2.876-1.04l.141-.081 4.779-2.758a.795.795 0 00.392-.681v-6.737l2.02 1.168a.071.071 0 01.038.052v5.583a4.504 4.504 0 01-4.494 4.494zM3.6 18.304a4.47 4.47 0 01-.535-3.014l.142.085 4.783 2.759a.771.771 0 00.78 0l5.843-3.369v2.332a.08.08 0 01-.033.062L9.74 19.95a4.5 4.5 0 01-6.14-1.646zM2.34 7.896a4.485 4.485 0 012.366-1.973V11.6a.766.766 0 00.388.676l5.815 3.355-2.02 1.168a.076.076 0 01-.071 0l-4.83-2.786A4.504 4.504 0 012.34 7.872zm16.597 3.855l-5.833-3.387L15.119 7.2a.076.076 0 01.071 0l4.83 2.791a4.494 4.494 0 01-.676 8.105v-5.678a.79.79 0 00-.407-.667zm2.01-3.023l-.141-.085-4.774-2.782a.776.776 0 00-.785 0L9.409 9.23V6.897a.066.066 0 01.028-.061l4.83-2.787a4.5 4.5 0 016.68 4.66zm-12.64 4.135l-2.02-1.164a.08.08 0 01-.038-.057V6.075a4.5 4.5 0 017.375-3.453l-.142.08L8.704 5.46a.795.795 0 00-.393.681zm1.097-2.365l2.602-1.5 2.607 1.5v2.999l-2.597 1.5-2.607-1.5z"/>
                </svg>
                <span class="text-[13px] font-display font-semibold">ChatGPT</span>
              </div>
              <div class="flex items-center gap-2 text-warm-400 hover:text-secondary transition-colors flex-shrink-0">
                <svg class="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M17.304 3.541h-3.672l6.696 16.918h3.672zm-10.608 0L0 20.459h3.744l1.38-3.588h7.068l1.38 3.588h3.744L10.608 3.541zm-.372 10.578l2.34-6.084 2.34 6.084z"/>
                </svg>
                <span class="text-[13px] font-display font-semibold">Claude</span>
              </div>
              <div class="flex items-center gap-2 text-warm-400 hover:text-secondary transition-colors flex-shrink-0">
                <svg class="w-5 h-5" viewBox="0 0 28 28" fill="currentColor">
                  <path d="M14 0c-.4 5.6-2.1 9.8-6.8 12.3C2.5 14.8 0 16 0 16s2 .6 6.6 2.6c4.7 2.5 6.4 6.7 6.8 12.3.4-5.6 2.1-9.8 6.8-12.3C24.8 16.1 28 16 28 16s-2-.6-6.6-2.6C16.7 10.9 14.4 5.6 14 0z"/>
                </svg>
                <span class="text-[13px] font-display font-semibold">Gemini</span>
              </div>
              <div class="flex items-center gap-2 text-warm-400 hover:text-secondary transition-colors flex-shrink-0">
                <svg class="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M4 4h7v7H4zM13 4h7v7h-7zM4 13h7v7H4zM17 13v4h-4v-4h4zm-4 4h4v3h-7v-7h3v4z" fill-rule="evenodd"/>
                </svg>
                <span class="text-[13px] font-display font-semibold">Perplexity</span>
              </div>
              <div class="flex items-center gap-2 text-warm-400 hover:text-secondary transition-colors flex-shrink-0">
                <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="11" cy="11" r="8"/><path stroke-linecap="round" d="M21 21l-4.35-4.35"/>
                </svg>
                <span class="text-[13px] font-display font-semibold">SearchGPT</span>
              </div>
              <div class="flex items-center gap-2 text-warm-400 hover:text-secondary transition-colors flex-shrink-0">
                <svg class="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 14H9V8h2v8zm4 0h-2V8h2v8z"/>
                </svg>
                <span class="text-[13px] font-display font-semibold">Copilot</span>
              </div>
              <!-- Set 2 (duplicate for seamless loop) -->
              <div class="flex items-center gap-2 text-warm-400 hover:text-secondary transition-colors flex-shrink-0" aria-hidden="true">
                <svg class="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M22.282 9.821a5.985 5.985 0 00-.516-4.91 6.046 6.046 0 00-6.51-2.9A6.065 6.065 0 004.981 4.18a5.985 5.985 0 00-3.998 2.9 6.046 6.046 0 00.743 7.097 5.98 5.98 0 00.51 4.911 6.051 6.051 0 006.515 2.9A5.985 5.985 0 0013.26 24a6.056 6.056 0 005.772-4.206 5.99 5.99 0 003.997-2.9 6.056 6.056 0 00-.747-7.073zM13.26 22.43a4.476 4.476 0 01-2.876-1.04l.141-.081 4.779-2.758a.795.795 0 00.392-.681v-6.737l2.02 1.168a.071.071 0 01.038.052v5.583a4.504 4.504 0 01-4.494 4.494zM3.6 18.304a4.47 4.47 0 01-.535-3.014l.142.085 4.783 2.759a.771.771 0 00.78 0l5.843-3.369v2.332a.08.08 0 01-.033.062L9.74 19.95a4.5 4.5 0 01-6.14-1.646zM2.34 7.896a4.485 4.485 0 012.366-1.973V11.6a.766.766 0 00.388.676l5.815 3.355-2.02 1.168a.076.076 0 01-.071 0l-4.83-2.786A4.504 4.504 0 012.34 7.872zm16.597 3.855l-5.833-3.387L15.119 7.2a.076.076 0 01.071 0l4.83 2.791a4.494 4.494 0 01-.676 8.105v-5.678a.79.79 0 00-.407-.667zm2.01-3.023l-.141-.085-4.774-2.782a.776.776 0 00-.785 0L9.409 9.23V6.897a.066.066 0 01.028-.061l4.83-2.787a4.5 4.5 0 016.68 4.66zm-12.64 4.135l-2.02-1.164a.08.08 0 01-.038-.057V6.075a4.5 4.5 0 017.375-3.453l-.142.08L8.704 5.46a.795.795 0 00-.393.681zm1.097-2.365l2.602-1.5 2.607 1.5v2.999l-2.597 1.5-2.607-1.5z"/>
                </svg>
                <span class="text-[13px] font-display font-semibold">ChatGPT</span>
              </div>
              <div class="flex items-center gap-2 text-warm-400 hover:text-secondary transition-colors flex-shrink-0" aria-hidden="true">
                <svg class="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M17.304 3.541h-3.672l6.696 16.918h3.672zm-10.608 0L0 20.459h3.744l1.38-3.588h7.068l1.38 3.588h3.744L10.608 3.541zm-.372 10.578l2.34-6.084 2.34 6.084z"/>
                </svg>
                <span class="text-[13px] font-display font-semibold">Claude</span>
              </div>
              <div class="flex items-center gap-2 text-warm-400 hover:text-secondary transition-colors flex-shrink-0" aria-hidden="true">
                <svg class="w-5 h-5" viewBox="0 0 28 28" fill="currentColor">
                  <path d="M14 0c-.4 5.6-2.1 9.8-6.8 12.3C2.5 14.8 0 16 0 16s2 .6 6.6 2.6c4.7 2.5 6.4 6.7 6.8 12.3.4-5.6 2.1-9.8 6.8-12.3C24.8 16.1 28 16 28 16s-2-.6-6.6-2.6C16.7 10.9 14.4 5.6 14 0z"/>
                </svg>
                <span class="text-[13px] font-display font-semibold">Gemini</span>
              </div>
              <div class="flex items-center gap-2 text-warm-400 hover:text-secondary transition-colors flex-shrink-0" aria-hidden="true">
                <svg class="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M4 4h7v7H4zM13 4h7v7h-7zM4 13h7v7H4zM17 13v4h-4v-4h4zm-4 4h4v3h-7v-7h3v4z" fill-rule="evenodd"/>
                </svg>
                <span class="text-[13px] font-display font-semibold">Perplexity</span>
              </div>
              <div class="flex items-center gap-2 text-warm-400 hover:text-secondary transition-colors flex-shrink-0" aria-hidden="true">
                <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="11" cy="11" r="8"/><path stroke-linecap="round" d="M21 21l-4.35-4.35"/>
                </svg>
                <span class="text-[13px] font-display font-semibold">SearchGPT</span>
              </div>
              <div class="flex items-center gap-2 text-warm-400 hover:text-secondary transition-colors flex-shrink-0" aria-hidden="true">
                <svg class="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 14H9V8h2v8zm4 0h-2V8h2v8z"/>
                </svg>
                <span class="text-[13px] font-display font-semibold">Copilot</span>
              </div>
            </div>
            <!-- Edge fades -->
            <div class="absolute inset-y-0 left-0 w-12 bg-gradient-to-r from-warm-50 to-transparent pointer-events-none"></div>
            <div class="absolute inset-y-0 right-0 w-12 bg-gradient-to-l from-warm-50 to-transparent pointer-events-none"></div>
          </div>
        </div>
      </div>
    </section>

    <!-- ─── The Problem ─── -->
    <section id="problem" class="py-24 px-6 lg:px-8">
      <div class="max-w-5xl mx-auto">
        <div class="grid lg:grid-cols-[1fr,420px] gap-16 items-start">

          <!-- Left -->
          <div>
            <p class="section-label mb-4">The problem</p>
            <h2 class="font-display text-[2rem] sm:text-[2.5rem] font-bold tracking-tight leading-[1.1] mb-6">
              AI agents are the<br>new search engines.
            </h2>
            <p class="text-[16px] text-secondary leading-relaxed mb-8 max-w-[44ch]">
              Millions of people now skip Google entirely and ask ChatGPT, Claude, or Perplexity to recommend products, services, and places. AI answers instantly — and it only recommends businesses it can understand.
            </p>

            <!-- Animated stats -->
            <div class="border-l-4 border-accent pl-6 py-2 mb-5">
              <div class="font-display text-[2.2rem] font-bold text-primary tabular-nums counter-20b">40%</div>
              <p class="text-[13px] text-secondary mt-1">of product searches now start with AI assistants</p>
              <p class="text-[11px] text-muted mt-0.5">— Salesforce State of Commerce, 2025</p>
            </div>

            <div class="border border-border-light rounded-xl bg-warm-50 px-5 py-4 mb-8">
              <p class="text-[14px] text-primary font-display font-semibold leading-snug mb-1">
                "If AI can't find you, you're invisible to the next generation of customers."
              </p>
              <p class="text-[12px] text-muted">The shift is already happening — AI-referred traffic is growing 3× faster than organic search.</p>
            </div>

            <p class="text-[15px] text-secondary leading-relaxed max-w-[44ch]">
              Sites with AI readiness measures see up to <strong class="text-primary font-semibold">3x more referral traffic</strong> from AI assistants within 90 days. The window to be an early mover is closing fast.
            </p>
          </div>

          <!-- Right: Before/After comparison -->
          <div class="space-y-4">
            <p class="text-[11px] font-display font-semibold text-muted uppercase tracking-widest mb-5">The difference AI readiness makes</p>

            <!-- Without -->
            <div class="rounded-xl border border-score-bad/25 bg-score-bad/4 p-5">
              <div class="flex items-center gap-2.5 mb-4">
                <div class="w-7 h-7 rounded-full bg-score-bad/12 flex items-center justify-center">
                  <svg class="w-3.5 h-3.5 text-score-bad" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"/>
                  </svg>
                </div>
                <p class="text-[12px] font-display font-semibold text-score-bad uppercase tracking-wide">Without AI readiness</p>
              </div>
              <div class="space-y-2">
                <div class="flex items-center gap-2 text-[13px] text-secondary">
                  <span class="w-1 h-1 rounded-full bg-score-bad/50 flex-shrink-0"></span>
                  AI can't parse your business info
                </div>
                <div class="flex items-center gap-2 text-[13px] text-secondary">
                  <span class="w-1 h-1 rounded-full bg-score-bad/50 flex-shrink-0"></span>
                  Not mentioned in AI responses
                </div>
                <div class="flex items-center gap-2 text-[13px] text-secondary">
                  <span class="w-1 h-1 rounded-full bg-score-bad/50 flex-shrink-0"></span>
                  Competitors get the recommendation
                </div>
                <div class="flex items-center gap-2 text-[13px] text-secondary">
                  <span class="w-1 h-1 rounded-full bg-score-bad/50 flex-shrink-0"></span>
                  Invisible to 100M+ daily AI users
                </div>
              </div>
            </div>

            <!-- With -->
            <div class="rounded-xl border border-score-good/25 bg-score-good/4 p-5">
              <div class="flex items-center gap-2.5 mb-4">
                <div class="w-7 h-7 rounded-full bg-score-good/12 flex items-center justify-center">
                  <svg class="w-3.5 h-3.5 text-score-good" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/>
                  </svg>
                </div>
                <p class="text-[12px] font-display font-semibold text-score-good uppercase tracking-wide">With AI readiness</p>
              </div>
              <div class="space-y-2">
                <div class="flex items-center gap-2 text-[13px] text-secondary">
                  <span class="w-1 h-1 rounded-full bg-score-good/60 flex-shrink-0"></span>
                  AI understands your products & services
                </div>
                <div class="flex items-center gap-2 text-[13px] text-secondary">
                  <span class="w-1 h-1 rounded-full bg-score-good/60 flex-shrink-0"></span>
                  Recommended in relevant queries
                </div>
                <div class="flex items-center gap-2 text-[13px] text-secondary">
                  <span class="w-1 h-1 rounded-full bg-score-good/60 flex-shrink-0"></span>
                  Drives qualified AI-sourced traffic
                </div>
                <div class="flex items-center gap-2 text-[13px] text-secondary">
                  <span class="w-1 h-1 rounded-full bg-score-good/60 flex-shrink-0"></span>
                  3x referral traffic within 90 days
                </div>
              </div>
            </div>

            <!-- Mini notification popup -->
            <div class="notif-popup flex items-center gap-3 border border-score-good/30 bg-surface rounded-xl px-4 py-3 shadow-sm">
              <div class="w-8 h-8 rounded-full bg-score-good/15 flex items-center justify-center flex-shrink-0">
                <svg class="w-4 h-4 text-score-good" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6 6 0 00-9.33-5"/>
                  <path stroke-linecap="round" stroke-linejoin="round" d="M9 17v1a3 3 0 006 0v-1M9 7a3 3 0 015.33-1.9"/>
                </svg>
              </div>
              <div>
                <p class="text-[12px] font-display font-semibold text-primary">Your site was mentioned in 3 AI responses this week</p>
                <p class="text-[10px] text-muted mt-0.5">ChatGPT · Claude · Perplexity · Gemini · Copilot · AI Overview</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ─── How it works ─── -->
    <section id="how-it-works" class="py-24 px-6 lg:px-8 border-t border-border-light bg-warm-50">
      <div class="max-w-5xl mx-auto">
        <p class="section-label mb-4">How it works</p>
        <h2 class="font-display text-[2rem] font-bold tracking-tight mb-16 max-w-md leading-tight">
          From URL to actionable fixes in 30 seconds
        </h2>

        <div class="grid sm:grid-cols-3 gap-0 relative">
          <!-- Connector line -->
          <div class="hidden sm:block absolute top-7 left-[16.66%] right-[16.66%] h-px bg-border-light z-0"></div>

          <!-- Step 1 -->
          <div class="relative z-10 pr-8">
            <div class="step-visual mb-6">
              <div class="w-14 h-14 rounded-2xl bg-surface border border-border flex items-center justify-center mb-4 relative">
                <svg class="w-6 h-6 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                  <circle cx="12" cy="12" r="10"/>
                  <path stroke-linecap="round" d="M2 12h20M12 2a15.3 15.3 0 014 10 15.3 15.3 0 01-4 10 15.3 15.3 0 01-4-10 15.3 15.3 0 014-10z"/>
                </svg>
                <span class="absolute -top-2 -right-2 w-5 h-5 rounded-full bg-accent text-white font-display font-bold text-[10px] flex items-center justify-center">1</span>
              </div>
              <!-- Mini domain input simulation -->
              <div class="flex items-center gap-2 border border-border-light rounded-lg px-3 py-2 bg-surface max-w-[180px]">
                <svg class="w-3 h-3 text-warm-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/></svg>
                <span class="text-[11px] text-primary font-body step1-type">yoursite.com</span>
                <span class="w-0.5 h-3 bg-accent step-cursor ml-auto flex-shrink-0"></span>
              </div>
            </div>
            <h3 class="font-display font-semibold text-primary mb-2">Enter your URL</h3>
            <p class="text-[13px] text-secondary leading-relaxed">Paste any URL. We detect your site type and start the analysis automatically.</p>
          </div>

          <!-- Step 2 -->
          <div class="relative z-10 px-4 sm:px-8 pt-12 sm:pt-0">
            <div class="step-visual mb-6">
              <div class="w-14 h-14 rounded-2xl bg-surface border border-border flex items-center justify-center mb-4 relative">
                <svg class="w-6 h-6 text-accent step-scan-spin" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                  <path stroke-linecap="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/>
                </svg>
                <span class="absolute -top-2 -right-2 w-5 h-5 rounded-full bg-accent text-white font-display font-bold text-[10px] flex items-center justify-center">2</span>
              </div>
              <!-- Mini scanning bars -->
              <div class="space-y-1.5 max-w-[180px]">
                <div class="h-1.5 rounded-full bg-warm-200 overflow-hidden">
                  <div class="h-full bg-accent rounded-full scan-bar-1" style="width:0%"></div>
                </div>
                <div class="h-1.5 rounded-full bg-warm-200 overflow-hidden">
                  <div class="h-full bg-accent rounded-full scan-bar-2" style="width:0%"></div>
                </div>
                <div class="h-1.5 rounded-full bg-warm-200 overflow-hidden">
                  <div class="h-full bg-score-medium rounded-full scan-bar-3" style="width:0%"></div>
                </div>
                <div class="h-1.5 rounded-full bg-warm-200 overflow-hidden">
                  <div class="h-full bg-accent rounded-full scan-bar-4" style="width:0%"></div>
                </div>
                <div class="h-1.5 rounded-full bg-warm-200 overflow-hidden">
                  <div class="h-full bg-score-good rounded-full scan-bar-5" style="width:0%"></div>
                </div>
              </div>
            </div>
            <h3 class="font-display font-semibold text-primary mb-2">Get your AI readiness score</h3>
            <p class="text-[13px] text-secondary leading-relaxed">18+ checks across protocols, structured data, and agent accessibility — scored out of 100 in real time.</p>
          </div>

          <!-- Step 3 -->
          <div class="relative z-10 pl-4 sm:pl-8 pt-12 sm:pt-0">
            <div class="step-visual mb-6">
              <div class="w-14 h-14 rounded-2xl bg-surface border border-border flex items-center justify-center mb-4 relative">
                <svg class="w-6 h-6 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z"/>
                </svg>
                <span class="absolute -top-2 -right-2 w-5 h-5 rounded-full bg-accent text-white font-display font-bold text-[10px] flex items-center justify-center">3</span>
              </div>
              <!-- Mini score reveal -->
              <div class="flex items-center gap-3 max-w-[180px]">
                <div class="score-reveal-ring w-12 h-12 rounded-full border-[3px] border-score-good flex items-center justify-center flex-shrink-0">
                  <span class="font-display font-bold text-sm text-score-good score-reveal-num">74</span>
                </div>
                <div>
                  <p class="text-[11px] font-display font-semibold text-primary">Grade B</p>
                  <p class="text-[10px] text-secondary">Good — 4 fixes</p>
                </div>
              </div>
            </div>
            <h3 class="font-display font-semibold text-primary mb-2">Fix issues &amp; get found</h3>
            <p class="text-[13px] text-secondary leading-relaxed">A score out of 100, a letter grade, and prioritized code fixes so AI agents can finally find you.</p>
          </div>
        </div>
      </div>
    </section>

    <!-- ─── What we check — accordion ─── -->
    <section id="checks" class="py-24 px-6 lg:px-8 border-t border-border-light">
      <div class="max-w-5xl mx-auto">
        <div class="grid lg:grid-cols-[340px,1fr] gap-16">

          <!-- Left: sticky label + title -->
          <div>
            <p class="section-label mb-4">What we check</p>
            <h2 class="font-display text-[2rem] font-bold tracking-tight leading-tight mb-6">
              Five categories,<br>scored out of 100
            </h2>
            <p class="text-[15px] text-secondary leading-relaxed mb-8">
              Each category measures a different dimension of how well AI agents can interact with your site.
            </p>
            <!-- Total score bar -->
            <div class="border border-border rounded-xl p-5 bg-warm-50">
              <p class="text-[11px] font-display font-semibold text-muted uppercase tracking-wider mb-4">Score breakdown</p>
              <div class="space-y-3">
                <div v-for="(cat, idx) in categories" :key="idx">
                  <div class="flex justify-between text-[12px] mb-1">
                    <span :class="openCategory === idx ? 'text-accent font-display font-semibold' : 'text-secondary'">{{ cat.name }}</span>
                    <span class="text-muted tabular-nums font-display">{{ cat.points }} pts</span>
                  </div>
                  <div class="h-1 bg-warm-200 rounded-full overflow-hidden">
                    <div
                      class="h-full rounded-full transition-all duration-500"
                      :class="openCategory === idx ? 'bg-accent' : 'bg-warm-300'"
                      :style="`width: ${cat.points}%`"
                    ></div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Right: accordion -->
          <div class="divide-y divide-border-light">
            <div
              v-for="(cat, idx) in categories"
              :key="idx"
              class="py-1"
            >
              <button
                @click="openCategory = openCategory === idx ? -1 : idx"
                class="w-full text-left py-4 flex items-center gap-4 focus-visible:outline-none"
              >
                <div
                  class="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 transition-colors duration-200"
                  :class="openCategory === idx ? 'bg-accent text-white' : 'bg-warm-100 text-warm-500'"
                >
                  <svg class="w-4.5 h-4.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                    <path stroke-linecap="round" stroke-linejoin="round" :d="cat.icon"/>
                  </svg>
                </div>
                <div class="flex-1 min-w-0">
                  <p class="font-display font-semibold text-primary text-[15px]">{{ cat.name }}</p>
                  <p class="text-[12px] text-muted mt-0.5">{{ cat.points }} points</p>
                </div>
                <svg
                  class="w-4 h-4 text-warm-400 flex-shrink-0 transition-transform duration-200"
                  :class="openCategory === idx ? 'rotate-180' : ''"
                  fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"
                >
                  <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7"/>
                </svg>
              </button>

              <div v-if="openCategory === idx" class="pb-5 pl-[52px] pr-2">
                <p class="text-[14px] text-secondary leading-relaxed mb-4">{{ cat.desc }}</p>
                <div class="flex flex-wrap gap-2">
                  <span
                    v-for="check in cat.checks"
                    :key="check"
                    class="inline-flex items-center gap-1.5 text-[11px] font-display text-secondary bg-warm-100 border border-border-light rounded-full px-3 py-1"
                  >
                    <span class="w-1 h-1 rounded-full bg-accent/50"></span>
                    {{ check }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ─── Pro value prop ─── -->
    <section class="py-24 px-6 lg:px-8 border-t border-border-light bg-primary text-white relative overflow-hidden">
      <!-- Subtle grid overlay on dark -->
      <div class="absolute inset-0 pointer-events-none opacity-5" style="background-image: linear-gradient(to right, #fff 1px, transparent 1px), linear-gradient(to bottom, #fff 1px, transparent 1px); background-size: 48px 48px;"></div>

      <div class="max-w-5xl mx-auto relative">
        <p class="section-label mb-4 text-white/40">Feature highlights</p>
        <div class="grid lg:grid-cols-[1fr,auto] gap-10 mb-16 items-end">
          <h2 class="font-display text-[2rem] sm:text-[2.5rem] font-bold tracking-tight leading-tight text-white">
            Everything you need to be<br>
            <span class="text-accent">visible to LLMs.</span>
          </h2>
          <a href="/pricing" class="inline-flex items-center gap-2 text-[13px] font-display font-semibold text-accent border border-accent/30 rounded-lg px-4 py-2.5 hover:bg-accent hover:text-white transition-all duration-150 whitespace-nowrap flex-shrink-0">
            View Pro pricing
            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7"/>
            </svg>
          </a>
        </div>

        <div class="grid sm:grid-cols-2 lg:grid-cols-4 gap-8">
          <div class="border-l border-accent/30 pl-5 group">
            <span class="inline-block font-display font-bold text-accent text-[11px] mb-3 tracking-wider">01</span>
            <h3 class="font-display font-semibold text-white mb-2 text-[15px]">llms.txt</h3>
            <p class="text-[13px] text-white/50 leading-relaxed">
              Tell AI agents about your business in their native language. We generate and host the file for you.
            </p>
          </div>
          <div class="border-l border-accent/30 pl-5 group">
            <span class="inline-block font-display font-bold text-accent text-[11px] mb-3 tracking-wider">02</span>
            <h3 class="font-display font-semibold text-white mb-2 text-[15px]">Schema.org</h3>
            <p class="text-[13px] text-white/50 leading-relaxed">
              Structured data AI can read and trust. We audit your JSON-LD and surface exactly what's missing.
            </p>
          </div>
          <div class="border-l border-accent/30 pl-5 group">
            <span class="inline-block font-display font-bold text-accent text-[11px] mb-3 tracking-wider">03</span>
            <h3 class="font-display font-semibold text-white mb-2 text-[15px]">Agent Simulator</h3>
            <p class="text-[13px] text-white/50 leading-relaxed">
              Watch ChatGPT navigate your site. See exactly what it reads, skips, and why it recommends your competitors.
            </p>
          </div>
          <div class="border-l border-accent/30 pl-5 group">
            <span class="inline-block font-display font-bold text-accent text-[11px] mb-3 tracking-wider">04</span>
            <h3 class="font-display font-semibold text-white mb-2 text-[15px]">Hosted AI Files</h3>
            <p class="text-[13px] text-white/50 leading-relaxed">
              We serve your AI presence for you. No deployment needed — your llms.txt and schema files stay up to date automatically.
            </p>
          </div>
        </div>
      </div>
    </section>

    <!-- ─── FAQ ─── -->
    <section id="faq" class="py-24 px-6 lg:px-8 border-t border-border-light">
      <div class="max-w-5xl mx-auto">
        <div class="grid lg:grid-cols-[280px,1fr] gap-16">
          <div>
            <p class="section-label mb-4">FAQ</p>
            <h2 class="font-display text-[2rem] font-bold tracking-tight leading-tight">
              Common<br>questions
            </h2>
          </div>
          <div class="divide-y divide-border-light">
            <div v-for="(faq, idx) in faqs" :key="idx">
              <button
                @click="toggleFaq(idx)"
                class="w-full text-left py-4 flex items-start justify-between gap-4 focus-visible:outline-none"
              >
                <span class="text-[15px] font-display font-semibold text-primary leading-snug">{{ faq.q }}</span>
                <svg
                  class="w-4 h-4 text-warm-400 flex-shrink-0 mt-1 transition-transform duration-200"
                  :class="{ 'rotate-180': openFaq === idx }"
                  fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"
                >
                  <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7"/>
                </svg>
              </button>
              <div v-if="openFaq === idx" class="pb-5 -mt-1 pr-6">
                <p class="text-[14px] text-secondary leading-relaxed">{{ faq.a }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ─── Bottom CTA ─── -->
    <section class="py-24 px-6 lg:px-8 border-t border-border-light bg-warm-50">
      <div class="max-w-2xl mx-auto text-center">
        <p class="section-label mb-6">Free scan</p>
        <h2 class="font-display text-[2rem] sm:text-[2.6rem] font-bold tracking-tight leading-[1.1] mb-5">
          Check if AI agents can find<br>
          your website.
        </h2>
        <p class="text-[16px] text-secondary mb-10 max-w-[44ch] mx-auto leading-relaxed">
          Free, 30 seconds. No signup required. See your AI visibility score and exactly what to fix.
        </p>
        <form @submit.prevent="handleScan(domainBottom)" class="group">
          <div class="relative flex items-center max-w-lg mx-auto border border-warm-300 rounded-xl bg-surface transition-all duration-200 focus-within:border-accent focus-within:ring-4 focus-within:ring-accent/10 hover:border-warm-400 shadow-sm">
            <div class="flex-shrink-0 pl-4 pr-2">
              <svg class="w-4 h-4 text-warm-400 transition-colors duration-150 group-focus-within:text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/>
                <path stroke-linecap="round" d="M2 12h20M12 2a15.3 15.3 0 014 10 15.3 15.3 0 01-4 10 15.3 15.3 0 01-4-10 15.3 15.3 0 014-10z"/>
              </svg>
            </div>
            <input
              v-model="domainBottom"
              type="text"
              placeholder="yourdomain.com"
              class="flex-1 bg-transparent py-3.5 text-[15px] text-primary placeholder-warm-400 font-body focus:outline-none"
              :disabled="loading"
              autocomplete="url"
              aria-label="Enter your domain"
            />
            <button
              type="submit"
              class="flex-shrink-0 m-1.5 btn-primary rounded-lg px-5 py-2.5 text-[13px]"
              :disabled="loading || !domainBottom.trim()"
            >
              <svg v-if="loading" class="w-3.5 h-3.5 mr-1.5 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
              </svg>
              {{ loading ? 'Scanning…' : 'Check my site' }}
            </button>
          </div>
        </form>
        <p class="mt-4 text-[12px] text-muted">No registration required · Free forever</p>
      </div>
    </section>

    <!-- ─── Footer ─── -->
    <footer class="border-t border-border-light py-8 px-6 lg:px-8">
      <div class="max-w-5xl mx-auto flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div class="flex items-center gap-2 text-sm text-secondary">
          <svg class="w-4 h-4 text-accent" viewBox="0 0 24 24" fill="none">
            <path d="M12 2L4 20h4l1.5-4h5L16 20h4L12 2zm0 7l2 5h-4l2-5z" fill="currentColor"/>
            <path d="M20 8a10 10 0 00-4-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" opacity="0.5"/>
            <path d="M22 6a14 14 0 00-6-5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" opacity="0.3"/>
          </svg>
          AgentCheck
        </div>
        <div class="flex items-center gap-5 text-xs text-muted">
          <router-link to="/privacy" class="hover:text-secondary transition-colors">Privacy Policy</router-link>
          <router-link to="/terms" class="hover:text-secondary transition-colors">Terms of Service</router-link>
          <router-link to="/imprint" class="hover:text-secondary transition-colors">Imprint</router-link>
          <a href="https://github.com/lennystepn-hue/agentcheck" target="_blank" rel="noopener" class="hover:text-secondary transition-colors">GitHub</a>
          <span>&copy; {{ new Date().getFullYear() }} AgentCheck</span>
        </div>
      </div>
    </footer>

  </div>
</template>

<style scoped>
/* ── Chat simulation ── */
.chat-msg-user {
  animation: fadeInUp 0.4s ease-out 0.3s both;
}

.chat-typing {
  animation: fadeInUp 0.3s ease-out 1s both, fadeOut 0.25s ease-in 2.8s forwards;
}

.chat-dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #9C9789;
  animation: chatDotBounce 1.2s ease-in-out infinite;
}
.chat-dot:nth-child(2) { animation-delay: 0.2s; }
.chat-dot:nth-child(3) { animation-delay: 0.4s; }

@keyframes chatDotBounce {
  0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
  30% { transform: translateY(-4px); opacity: 1; }
}

.chat-response {
  animation: fadeInUp 0.4s ease-out 3.1s both;
}

.chat-result-1 {
  animation: slideInResult 0.35s ease-out 3.2s both;
}
.chat-result-2 {
  animation: slideInResult 0.35s ease-out 3.5s both;
}
.chat-result-3 {
  animation: slideInResult 0.35s ease-out 3.8s both;
}

@keyframes slideInResult {
  from { opacity: 0; transform: translateX(-6px); }
  to { opacity: 1; transform: translateX(0); }
}

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes fadeOut {
  from { opacity: 1; height: auto; }
  to { opacity: 0; height: 0; overflow: hidden; }
}

/* ── Logo marquee ── */
.logo-marquee {
  animation: marqueeScroll 22s linear infinite;
  width: max-content;
}
.logo-marquee:hover {
  animation-play-state: paused;
}

@keyframes marqueeScroll {
  from { transform: translateX(0); }
  to { transform: translateX(-50%); }
}

/* ── Step animations ── */
.step-cursor {
  animation: blink 1s step-end infinite;
  animation-delay: 0.8s;
}
@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

.scan-bar-1 { animation: scanFill 0.6s ease-out 0.2s forwards; --fill: 85%; }
.scan-bar-2 { animation: scanFill 0.6s ease-out 0.5s forwards; --fill: 72%; }
.scan-bar-3 { animation: scanFill 0.6s ease-out 0.8s forwards; --fill: 55%; }
.scan-bar-4 { animation: scanFill 0.6s ease-out 1.1s forwards; --fill: 90%; }
.scan-bar-5 { animation: scanFill 0.6s ease-out 1.4s forwards; --fill: 80%; }

@keyframes scanFill {
  from { width: 0%; }
  to { width: var(--fill); }
}

.score-reveal-ring {
  animation: scoreReveal 0.8s cubic-bezier(0.34, 1.56, 0.64, 1) 0.5s both;
}
@keyframes scoreReveal {
  from { opacity: 0; transform: scale(0.6); }
  to { opacity: 1; transform: scale(1); }
}

.score-reveal-num {
  animation: numCount 1s ease-out 0.8s both;
}

/* ── Notification popup ── */
.notif-popup {
  animation: notifSlide 0.5s cubic-bezier(0.34, 1.56, 0.64, 1) 1s both;
}
@keyframes notifSlide {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

/* ── Stat counter ── */
.counter-20b {
  animation: countUp 1.5s ease-out 0.3s both;
}
/* Visual only — number is static, animation adds the punch */
@keyframes countUp {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
