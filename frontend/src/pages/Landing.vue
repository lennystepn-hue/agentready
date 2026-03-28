<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { startScan } from '../api.js'
import { isLoggedIn, user } from '../auth.js'

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

const categories = [
  {
    name: 'Protocol Readiness',
    points: '20 pts',
    checks: ['UCP Endpoint', 'ai.txt', 'llms.txt', 'robots.txt AI rules'],
    desc: 'Can AI agents discover and connect to your shop through standard protocols?',
  },
  {
    name: 'Structured Data',
    points: '25 pts',
    checks: ['JSON-LD markup', 'Product Schema', 'Offer Schema', 'Organization', 'Breadcrumbs'],
    desc: 'Is your product catalog described in machine-readable formats?',
  },
  {
    name: 'Agent Accessibility',
    points: '20 pts',
    checks: ['Response time', 'JS dependency', 'API availability', 'URL structure'],
    desc: 'Can agents navigate and read your site without a browser?',
  },
  {
    name: 'Transaction Readiness',
    points: '20 pts',
    checks: ['Guest checkout', 'Payment methods', 'Shipping info', 'Return policy'],
    desc: 'Is your shop ready for programmatic purchasing?',
  },
  {
    name: 'Trust Signals',
    points: '15 pts',
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
    q: 'Do you store my data?',
    a: 'Scan results are stored temporarily so you can share your report link. We do not track visitors or sell data.',
  },
  {
    q: 'Who is this for?',
    a: 'E-commerce shop owners, SEO managers, and technical leads who want their products discoverable by AI shopping agents like ChatGPT, Perplexity, and Google Gemini.',
  },
]

const openFaq = ref(null)
function toggleFaq(idx) {
  openFaq.value = openFaq.value === idx ? null : idx
}
</script>

<template>
  <div class="flex-1 flex flex-col">
    <!-- ─── Nav ─── -->
    <nav class="sticky top-0 z-50 bg-page/95 backdrop-blur-sm border-b border-border-light">
      <div class="max-w-5xl mx-auto px-6 lg:px-8 h-14 flex items-center justify-between">
        <div class="flex items-center gap-2">
          <svg class="w-5 h-5 text-accent" viewBox="0 0 24 24" fill="none">
            <path d="M12 2L4 20h4l1.5-4h5L16 20h4L12 2zm0 7l2 5h-4l2-5z" fill="currentColor"/>
            <path d="M20 8a10 10 0 00-4-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" opacity="0.5"/>
            <path d="M22 6a14 14 0 00-6-5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" opacity="0.3"/>
          </svg>
          <span class="font-display font-bold text-[15px] tracking-tight">AgentCheck</span>
        </div>
        <div class="flex items-center gap-6">
          <a href="#how-it-works" class="hidden sm:block text-[13px] text-secondary hover:text-primary transition-colors">How it works</a>
          <a href="#checks" class="hidden sm:block text-[13px] text-secondary hover:text-primary transition-colors">Checks</a>
          <a href="#faq" class="hidden sm:block text-[13px] text-secondary hover:text-primary transition-colors">FAQ</a>
          <router-link to="/pricing" class="hidden sm:block text-[13px] text-secondary hover:text-primary transition-colors">Pricing</router-link>
          <template v-if="isLoggedIn">
            <router-link to="/dashboard" class="hidden sm:block text-[13px] text-secondary hover:text-primary transition-colors">Dashboard</router-link>
            <div
              class="w-7 h-7 rounded-full bg-accent text-white flex items-center justify-center text-xs font-display font-bold"
              :title="user?.email"
            >
              {{ user?.email?.[0]?.toUpperCase() || '?' }}
            </div>
          </template>
          <router-link v-else to="/login" class="hidden sm:block text-[13px] text-secondary hover:text-primary transition-colors">Sign in</router-link>
          <a
            href="https://github.com/lennystepn-hue/agentready"
            target="_blank"
            rel="noopener"
            class="text-secondary hover:text-primary transition-colors"
            aria-label="View source on GitHub"
          >
            <svg class="w-[18px] h-[18px]" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z" />
            </svg>
          </a>
        </div>
      </div>
    </nav>

    <!-- ─── Hero ─── -->
    <section class="pt-20 sm:pt-28 pb-24 px-6 lg:px-8">
      <div class="max-w-5xl mx-auto">
        <div class="grid lg:grid-cols-[1fr,340px] gap-16 items-start">
          <!-- Left: headline + form -->
          <div class="animate-fade-in">
            <p class="text-[13px] font-display font-semibold text-accent tracking-wide uppercase mb-5">Free &amp; open source scanner</p>

            <h1 class="font-display text-[2.5rem] sm:text-[3.25rem] font-bold tracking-tight leading-[1.08] text-primary">
              How discoverable is<br class="hidden sm:block" />
              your shop for<br class="hidden sm:block" />
              AI&nbsp;Agents?
            </h1>

            <p class="mt-6 text-[17px] text-secondary leading-relaxed max-w-[52ch]">
              AI agents are the new way people discover and buy products. If your
              shop isn't machine-readable, AI assistants will recommend your
              competitors instead. Scan your site, fix what's broken, and start
              getting found.
            </p>

            <!-- Scan form -->
            <form
              @submit.prevent="handleScan(domain)"
              class="mt-10 flex flex-col sm:flex-row gap-3 max-w-md"
            >
              <input
                v-model="domain"
                type="text"
                placeholder="your-shop.com"
                class="input-field flex-1"
                :disabled="loading"
                autocomplete="url"
              />
              <button
                type="submit"
                class="btn-primary whitespace-nowrap px-6"
                :disabled="loading || !domain.trim()"
              >
                <svg v-if="loading" class="w-4 h-4 mr-2 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                {{ loading ? 'Starting...' : 'Run scan' }}
              </button>
            </form>

            <p v-if="error" class="mt-3 text-sm text-score-bad">{{ error }}</p>

            <p class="mt-4 text-xs text-muted">
              No registration required. Results in under 30 seconds.
            </p>

            <!-- AI Platform Logos — in hero -->
            <div class="mt-10 pt-8 border-t border-border-light">
              <p class="text-[11px] text-warm-400 tracking-widest uppercase font-display mb-4">Make your shop visible to</p>
              <div class="flex items-center gap-7 flex-wrap">
                <!-- OpenAI / ChatGPT -->
                <div class="flex items-center gap-2 text-warm-500">
                  <svg class="w-6 h-6" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M22.282 9.821a5.985 5.985 0 0 0-.516-4.91 6.046 6.046 0 0 0-6.51-2.9A6.065 6.065 0 0 0 4.981 4.18a5.985 5.985 0 0 0-3.998 2.9 6.046 6.046 0 0 0 .743 7.097 5.98 5.98 0 0 0 .51 4.911 6.051 6.051 0 0 0 6.515 2.9A5.985 5.985 0 0 0 13.26 24a6.056 6.056 0 0 0 5.772-4.206 5.99 5.99 0 0 0 3.997-2.9 6.056 6.056 0 0 0-.747-7.073zM13.26 22.43a4.476 4.476 0 0 1-2.876-1.04l.141-.081 4.779-2.758a.795.795 0 0 0 .392-.681v-6.737l2.02 1.168a.071.071 0 0 1 .038.052v5.583a4.504 4.504 0 0 1-4.494 4.494zM3.6 18.304a4.47 4.47 0 0 1-.535-3.014l.142.085 4.783 2.759a.771.771 0 0 0 .78 0l5.843-3.369v2.332a.08.08 0 0 1-.033.062L9.74 19.95a4.5 4.5 0 0 1-6.14-1.646zM2.34 7.896a4.485 4.485 0 0 1 2.366-1.973V11.6a.766.766 0 0 0 .388.676l5.815 3.355-2.02 1.168a.076.076 0 0 1-.071 0l-4.83-2.786A4.504 4.504 0 0 1 2.34 7.872zm16.597 3.855l-5.833-3.387L15.119 7.2a.076.076 0 0 1 .071 0l4.83 2.791a4.494 4.494 0 0 1-.676 8.105v-5.678a.79.79 0 0 0-.407-.667zm2.01-3.023l-.141-.085-4.774-2.782a.776.776 0 0 0-.785 0L9.409 9.23V6.897a.066.066 0 0 1 .028-.061l4.83-2.787a4.5 4.5 0 0 1 6.68 4.66zm-12.64 4.135l-2.02-1.164a.08.08 0 0 1-.038-.057V6.075a4.5 4.5 0 0 1 7.375-3.453l-.142.08L8.704 5.46a.795.795 0 0 0-.393.681zm1.097-2.365l2.602-1.5 2.607 1.5v2.999l-2.597 1.5-2.607-1.5z"/>
                  </svg>
                  <span class="text-[15px] font-display font-semibold">ChatGPT</span>
                </div>
                <!-- Claude -->
                <div class="flex items-center gap-2 text-warm-500">
                  <svg class="w-6 h-6" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M17.304 3.541h-3.672l6.696 16.918h3.672zm-10.608 0L0 20.459h3.744l1.38-3.588h7.068l1.38 3.588h3.744L10.608 3.541zm-.372 10.578l2.34-6.084 2.34 6.084z"/>
                  </svg>
                  <span class="text-[15px] font-display font-semibold">Claude</span>
                </div>
                <!-- Gemini -->
                <div class="flex items-center gap-2 text-warm-500">
                  <svg class="w-6 h-6" viewBox="0 0 28 28" fill="currentColor">
                    <path d="M14 0c-.4 5.6-2.1 9.8-6.8 12.3C2.5 14.8 0 16 0 16s2 .6 6.6 2.6c4.7 2.5 6.4 6.7 6.8 12.3.4-5.6 2.1-9.8 6.8-12.3C24.8 16.1 28 16 28 16s-2-.6-6.6-2.6C16.7 10.9 14.4 5.6 14 0z"/>
                  </svg>
                  <span class="text-[15px] font-display font-semibold">Gemini</span>
                </div>
                <!-- Perplexity -->
                <div class="flex items-center gap-2 text-warm-500">
                  <svg class="w-6 h-6" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M4 4h7v7H4zM13 4h7v7h-7zM4 13h7v7H4zM17 13v4h-4v-4h4zm-4 4h4v3h-7v-7h3v4z" fill-rule="evenodd"/>
                  </svg>
                  <span class="text-[15px] font-display font-semibold">Perplexity</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Right: Example report preview -->
          <div class="hidden lg:block animate-slide-up" style="animation-delay: 150ms">
            <div class="border border-border rounded-lg p-6 bg-surface">
              <p class="text-[11px] font-display font-semibold text-muted uppercase tracking-wider mb-4">Example report</p>
              <!-- Mini score -->
              <div class="flex items-center gap-4 mb-5">
                <div class="w-14 h-14 rounded-full border-[3px] border-score-bad flex items-center justify-center">
                  <span class="font-display font-bold text-lg text-score-bad">28</span>
                </div>
                <div>
                  <p class="font-display font-semibold text-sm text-primary">example-shop.de</p>
                  <p class="text-xs text-muted">Grade E — needs work</p>
                </div>
              </div>
              <!-- Mini bars -->
              <div class="space-y-2.5">
                <div>
                  <div class="flex justify-between text-[11px] mb-1"><span class="text-secondary">Protocol</span><span class="text-muted tabular-nums">4/20</span></div>
                  <div class="h-1 bg-warm-200 rounded-full"><div class="h-full bg-score-bad rounded-full" style="width: 20%"></div></div>
                </div>
                <div>
                  <div class="flex justify-between text-[11px] mb-1"><span class="text-secondary">Structured Data</span><span class="text-muted tabular-nums">8/25</span></div>
                  <div class="h-1 bg-warm-200 rounded-full"><div class="h-full bg-score-bad rounded-full" style="width: 32%"></div></div>
                </div>
                <div>
                  <div class="flex justify-between text-[11px] mb-1"><span class="text-secondary">Accessibility</span><span class="text-muted tabular-nums">11/20</span></div>
                  <div class="h-1 bg-warm-200 rounded-full"><div class="h-full bg-score-medium rounded-full" style="width: 55%"></div></div>
                </div>
                <div>
                  <div class="flex justify-between text-[11px] mb-1"><span class="text-secondary">Transaction</span><span class="text-muted tabular-nums">2/20</span></div>
                  <div class="h-1 bg-warm-200 rounded-full"><div class="h-full bg-score-bad rounded-full" style="width: 10%"></div></div>
                </div>
                <div>
                  <div class="flex justify-between text-[11px] mb-1"><span class="text-secondary">Trust</span><span class="text-muted tabular-nums">3/15</span></div>
                  <div class="h-1 bg-warm-200 rounded-full"><div class="h-full bg-score-bad rounded-full" style="width: 20%"></div></div>
                </div>
              </div>
              <!-- Mini fixes -->
              <div class="mt-5 pt-4 border-t border-border-light">
                <p class="text-[11px] font-display font-semibold text-muted uppercase tracking-wider mb-2">Top fixes</p>
                <div class="space-y-1.5">
                  <div class="flex items-center gap-2 text-xs"><span class="w-1.5 h-1.5 rounded-full bg-score-bad flex-shrink-0"></span><span class="text-secondary">Add UCP endpoint</span></div>
                  <div class="flex items-center gap-2 text-xs"><span class="w-1.5 h-1.5 rounded-full bg-score-bad flex-shrink-0"></span><span class="text-secondary">Add Product Schema</span></div>
                  <div class="flex items-center gap-2 text-xs"><span class="w-1.5 h-1.5 rounded-full bg-score-medium flex-shrink-0"></span><span class="text-secondary">Create ai.txt file</span></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ─── Stats bar + AI logos ─── -->
    <section class="border-y border-border-light bg-warm-50">
      <div class="max-w-5xl mx-auto px-6 lg:px-8 py-8">
        <!-- Stats -->
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-8">
          <div>
            <p class="font-display text-2xl font-bold text-primary tabular-nums">18+</p>
            <p class="text-xs text-secondary mt-0.5">Individual checks</p>
          </div>
          <div>
            <p class="font-display text-2xl font-bold text-primary tabular-nums">5</p>
            <p class="text-xs text-secondary mt-0.5">Categories scored</p>
          </div>
          <div>
            <p class="font-display text-2xl font-bold text-primary tabular-nums">&lt;30s</p>
            <p class="text-xs text-secondary mt-0.5">Scan time</p>
          </div>
          <div>
            <p class="font-display text-2xl font-bold text-primary tabular-nums">100%</p>
            <p class="text-xs text-secondary mt-0.5">Free &amp; open source</p>
          </div>
        </div>
      </div>
    </section>

    <!-- ─── AI Visibility value prop ─── -->
    <section class="py-20 px-6 lg:px-8 bg-accent/[0.03] border-y border-accent/10">
      <div class="max-w-5xl mx-auto">
        <p class="section-label mb-3">Go beyond the score</p>
        <h2 class="font-display text-2xl font-bold tracking-tight mb-3 max-w-lg">
          Don't just score — get found
        </h2>
        <p class="text-secondary mb-14 max-w-xl text-[15px] leading-relaxed">
          With a Pro subscription, we don't just tell you what's broken. We help you fix it and continuously optimize your shop's AI visibility.
        </p>

        <div class="grid sm:grid-cols-3 gap-10">
          <div class="border-l-2 border-accent pl-5">
            <span class="inline-block font-display font-bold text-accent text-sm mb-2">01</span>
            <h3 class="font-display font-semibold text-primary mb-2">Deploy fix files automatically</h3>
            <p class="text-sm text-secondary leading-relaxed">
              We generate tailored ai.txt, llms.txt, Schema.org markup, and UCP configs — ready to deploy. Your dev team gets copy-paste code, or we guide them through the setup.
            </p>
          </div>
          <div class="border-l-2 border-accent pl-5">
            <span class="inline-block font-display font-bold text-accent text-sm mb-2">02</span>
            <h3 class="font-display font-semibold text-primary mb-2">Monitor AI bot traffic</h3>
            <p class="text-sm text-secondary leading-relaxed">
              Track which AI crawlers are visiting your shop — GPTBot, ClaudeBot, PerplexityBot, and more. Know when you start appearing in AI-powered shopping results.
            </p>
          </div>
          <div class="border-l-2 border-accent pl-5">
            <span class="inline-block font-display font-bold text-accent text-sm mb-2">03</span>
            <h3 class="font-display font-semibold text-primary mb-2">Weekly re-scans & alerts</h3>
            <p class="text-sm text-secondary leading-relaxed">
              Your score is re-checked every week. When something breaks or improves, you're the first to know. Stay ahead as AI commerce standards evolve.
            </p>
          </div>
        </div>
      </div>
    </section>

    <!-- ─── How it works ─── -->
    <section id="how-it-works" class="py-20 px-6 lg:px-8">
      <div class="max-w-5xl mx-auto">
        <p class="section-label mb-3">How it works</p>
        <h2 class="font-display text-2xl font-bold tracking-tight mb-14 max-w-md">
          Three steps from URL to actionable fixes
        </h2>

        <div class="grid sm:grid-cols-3 gap-12">
          <div>
            <span class="inline-flex items-center justify-center w-8 h-8 rounded-full bg-accent text-white font-display font-bold text-sm mb-4">1</span>
            <h3 class="font-display font-semibold text-primary mb-2">Enter your domain</h3>
            <p class="text-sm text-secondary leading-relaxed">
              Paste any e-commerce URL. We detect the homepage and start analyzing automatically.
            </p>
          </div>
          <div>
            <span class="inline-flex items-center justify-center w-8 h-8 rounded-full bg-accent text-white font-display font-bold text-sm mb-4">2</span>
            <h3 class="font-display font-semibold text-primary mb-2">We run 18+ checks</h3>
            <p class="text-sm text-secondary leading-relaxed">
              Our scanner evaluates protocols, structured data, accessibility, transaction readiness, and trust signals in real time.
            </p>
          </div>
          <div>
            <span class="inline-flex items-center justify-center w-8 h-8 rounded-full bg-accent text-white font-display font-bold text-sm mb-4">3</span>
            <h3 class="font-display font-semibold text-primary mb-2">Get score &amp; fixes</h3>
            <p class="text-sm text-secondary leading-relaxed">
              You receive a score out of 100, a letter grade, and prioritized fixes with code snippets for your dev team.
            </p>
          </div>
        </div>
      </div>
    </section>

    <!-- ─── What we check ─── -->
    <section id="checks" class="py-20 px-6 lg:px-8 border-t border-border-light bg-warm-50">
      <div class="max-w-5xl mx-auto">
        <p class="section-label mb-3">What we check</p>
        <h2 class="font-display text-2xl font-bold tracking-tight mb-4 max-w-md">
          Five categories, scored out of 100
        </h2>
        <p class="text-secondary mb-12 max-w-lg text-[15px] leading-relaxed">
          Each category measures a different dimension of how well AI agents can interact with your shop.
        </p>

        <div class="grid sm:grid-cols-2 lg:grid-cols-3 gap-x-8 gap-y-10">
          <div v-for="(cat, idx) in categories" :key="idx" class="group">
            <div class="flex items-baseline justify-between mb-2">
              <h3 class="font-display font-semibold text-primary">{{ cat.name }}</h3>
              <span class="text-xs text-muted font-display tabular-nums">{{ cat.points }}</span>
            </div>
            <p class="text-sm text-secondary leading-relaxed mb-3">{{ cat.desc }}</p>
            <div class="flex flex-wrap gap-1.5">
              <span
                v-for="check in cat.checks"
                :key="check"
                class="inline-block text-[11px] font-display text-muted bg-warm-100 rounded px-2 py-0.5"
              >
                {{ check }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ─── Quote / context ─── -->
    <section class="py-16 px-6 lg:px-8 border-t border-border-light">
      <div class="max-w-5xl mx-auto">
        <div class="grid sm:grid-cols-[1fr,1px,1fr] gap-10 sm:gap-12 items-start">
          <div>
            <h2 class="font-display text-xl font-bold tracking-tight mb-3">
              Most shops aren't ready
            </h2>
            <p class="text-sm text-secondary leading-relaxed">
              Our scans show the majority of online shops score below 30 out of 100.
              That means AI assistants can't reliably find their products, parse their
              catalog, or complete purchases — so they recommend competitors instead.
            </p>
          </div>
          <div class="hidden sm:block bg-border-light"></div>
          <blockquote class="pl-0 sm:pl-2">
            <p class="text-[17px] font-display font-medium text-primary leading-relaxed">
              "AI Agents will be responsible for
              <span class="text-accent font-bold">$20.9 billion</span>
              in retail spending by 2026."
            </p>
            <footer class="mt-3 text-sm text-muted">
              — Gartner Research, 2025
            </footer>
            <p class="mt-5 text-sm text-secondary leading-relaxed border-t border-border-light pt-4">
              Early data suggests shops that implement AI agent readiness measures see up to 3x more referral traffic from AI assistants within 90 days.
            </p>
          </blockquote>
        </div>
      </div>
    </section>

    <!-- ─── FAQ ─── -->
    <section id="faq" class="py-20 px-6 lg:px-8 border-t border-border-light bg-warm-50">
      <div class="max-w-5xl mx-auto">
        <div class="grid lg:grid-cols-[280px,1fr] gap-12">
          <div>
            <p class="section-label mb-3">FAQ</p>
            <h2 class="font-display text-2xl font-bold tracking-tight">
              Common questions
            </h2>
          </div>
          <div class="divide-y divide-border-light">
            <div v-for="(faq, idx) in faqs" :key="idx">
              <button
                @click="toggleFaq(idx)"
                class="w-full text-left py-4 flex items-start justify-between gap-4 focus-visible:outline-none focus-visible:bg-warm-100 -mx-2 px-2 rounded"
              >
                <span class="text-[15px] font-display font-semibold text-primary leading-snug">{{ faq.q }}</span>
                <svg
                  class="w-4 h-4 text-warm-400 flex-shrink-0 mt-1 transition-transform duration-200"
                  :class="{ 'rotate-180': openFaq === idx }"
                  fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"
                >
                  <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              <div v-if="openFaq === idx" class="pb-5 -mt-1 pl-0 pr-6">
                <p class="text-sm text-secondary leading-relaxed">{{ faq.a }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ─── Bottom CTA ─── -->
    <section class="py-20 px-6 lg:px-8 border-t border-border-light">
      <div class="max-w-5xl mx-auto text-center">
        <h2 class="font-display text-2xl sm:text-3xl font-bold tracking-tight mb-3">
          Check your shop now
        </h2>
        <p class="text-secondary mb-8 max-w-md mx-auto">
          Find out where you stand and what to improve. Free, no signup.
        </p>
        <form
          @submit.prevent="handleScan(domainBottom)"
          class="flex flex-col sm:flex-row gap-3 max-w-md mx-auto"
        >
          <input
            v-model="domainBottom"
            type="text"
            placeholder="your-shop.com"
            class="input-field flex-1"
            :disabled="loading"
            autocomplete="url"
          />
          <button
            type="submit"
            class="btn-primary whitespace-nowrap px-6"
            :disabled="loading || !domainBottom.trim()"
          >
            Run scan
          </button>
        </form>
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
