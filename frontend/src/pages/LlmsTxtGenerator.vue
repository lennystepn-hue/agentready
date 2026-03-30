<script setup>
import { ref, computed } from 'vue'
import AppHeader from '../components/AppHeader.vue'

const BASE_URL = import.meta.env.DEV
  ? 'http://localhost:8000'
  : window.location.origin

const domain = ref('')
const loading = ref(false)
const error = ref('')
const result = ref(null)   // { llms_txt: string, site_info: { name, type, language, pages_found } }
const copied = ref(false)

async function generate() {
  const v = domain.value.trim()
  if (!v) return

  error.value = ''
  result.value = null
  loading.value = true

  try {
    const res = await fetch(`${BASE_URL}/api/tools/generate-llms-txt`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ domain: v }),
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Generation failed.' }))
      throw new Error(err.detail || `HTTP ${res.status}`)
    }
    result.value = await res.json()
  } catch (e) {
    error.value = e.message || 'Could not generate llms.txt. Please try again.'
  } finally {
    loading.value = false
  }
}

async function copyToClipboard() {
  if (!result.value?.llms_txt) return
  try {
    await navigator.clipboard.writeText(result.value.llms_txt)
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
  } catch {
    // silently fail — user can manually select
  }
}

function downloadFile() {
  if (!result.value?.llms_txt) return
  const blob = new Blob([result.value.llms_txt], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'llms.txt'
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

function escHtml(s) {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
}

// Syntax-highlighted lines for the code block
const highlightedLines = computed(() => {
  if (!result.value?.llms_txt) return []
  return result.value.llms_txt.split('\n').map((line) => {
    if (/^#{1,3}\s/.test(line)) {
      return `<span class="llms-heading">${escHtml(line)}</span>`
    }
    if (/^[A-Za-z][A-Za-z\s\-]+:\s/.test(line)) {
      const idx = line.indexOf(':')
      return `<span class="llms-key">${escHtml(line.slice(0, idx))}</span><span class="llms-colon">${escHtml(line.slice(idx))}</span>`
    }
    if (/https?:\/\//.test(line)) {
      return escHtml(line).replace(
        /(https?:\/\/[^\s<>"]+)/g,
        '<span class="llms-url">$1</span>',
      )
    }
    if (line.startsWith('#') || line.trim() === '') {
      return `<span class="llms-comment">${escHtml(line)}</span>`
    }
    return escHtml(line)
  })
})

const faqs = [
  {
    q: 'What is llms.txt?',
    a: 'llms.txt is a plain-text file placed at the root of your website that helps AI language models — like ChatGPT, Claude, and Perplexity — understand what your website is about, what services you offer, and how to reference you accurately in AI-generated responses.',
  },
  {
    q: 'Why do I need llms.txt?',
    a: 'AI agents increasingly answer questions by reading and summarizing websites directly. Without llms.txt, AI may misrepresent your brand, miss key offerings, or skip your site entirely. llms.txt gives you a direct line to how AI describes your business.',
  },
  {
    q: 'Where do I put llms.txt?',
    a: 'Upload it to the root directory of your web server so it is accessible at yourdomain.com/llms.txt — the same place as your robots.txt or sitemap.xml. No code changes needed; it is just a static file.',
  },
  {
    q: 'Is this really free?',
    a: 'Yes, completely free, forever. No account required, no rate limits for reasonable use, no hidden fees. We built this tool to help every website owner get found by AI agents.',
  },
  {
    q: 'Will this affect my SEO?',
    a: 'llms.txt has no impact on traditional search engine indexing — Google, Bing, and others do not use it. It is specifically designed for AI discovery. Think of it as SEO for the AI era.',
  },
]
</script>

<template>
  <div class="flex-1 flex flex-col bg-grid">

    <!-- Header -->
    <AppHeader>
      <template #actions>
        <a href="#how-to-install" class="hidden sm:block text-[13px] text-secondary hover:text-primary transition-colors">How to install</a>
        <a href="#faq" class="hidden sm:block text-[13px] text-secondary hover:text-primary transition-colors">FAQ</a>
      </template>
    </AppHeader>

    <main class="flex-1">

      <!-- ─── Hero ─── -->
      <section class="pt-16 sm:pt-24 pb-16 px-6 lg:px-8 relative overflow-hidden">
        <div class="max-w-3xl mx-auto text-center animate-fade-in">

          <!-- Badge -->
          <p class="inline-flex items-center gap-2 text-[11px] font-display font-semibold text-accent tracking-widest uppercase mb-7 border border-accent/20 bg-accent/5 rounded-full px-3 py-1">
            <span class="w-1.5 h-1.5 rounded-full bg-accent animate-pulse-subtle"></span>
            No signup required
          </p>

          <h1 class="font-display text-[2.4rem] sm:text-[3.2rem] font-bold tracking-tight leading-[1.07] text-primary mb-5">
            Free llms.txt Generator
          </h1>

          <p class="text-[17px] text-secondary leading-relaxed max-w-[52ch] mx-auto mb-10">
            Create your AI discovery file in seconds.
            Help ChatGPT, Claude &amp; Perplexity understand your website.
          </p>

          <!-- URL Input pill -->
          <form @submit.prevent="generate" class="group max-w-xl mx-auto">
            <div class="relative flex items-center border border-warm-300 rounded-xl bg-surface transition-all duration-200 focus-within:border-accent focus-within:ring-4 focus-within:ring-accent/10 hover:border-warm-400 shadow-sm">
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
                placeholder="enter your website URL"
                class="flex-1 bg-transparent py-3.5 text-[15px] text-primary placeholder-warm-400 font-body focus:outline-none"
                :disabled="loading"
                autocomplete="url"
                aria-label="Enter your website URL"
              />
              <button
                type="submit"
                class="flex-shrink-0 m-1.5 btn-primary rounded-lg px-5 py-2.5 text-[13px]"
                :disabled="loading || !domain.trim()"
              >
                <svg v-if="loading" class="w-3.5 h-3.5 mr-1.5 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                </svg>
                {{ loading ? 'Generating…' : 'Generate' }}
              </button>
            </div>

            <p v-if="error" class="mt-3 text-sm text-score-bad text-left">{{ error }}</p>
          </form>

        </div>
      </section>

      <!-- ─── Result ─── -->
      <section v-if="result" class="pb-16 px-6 lg:px-8 animate-slide-up">
        <div class="max-w-3xl mx-auto">

          <!-- Site info card + status badge row -->
          <div class="flex flex-wrap items-start gap-4 mb-4">

            <div v-if="result.site_info" class="flex-1 min-w-0 bg-surface border border-border-light rounded-xl p-4 flex flex-wrap gap-x-6 gap-y-2.5">
              <div v-if="result.site_info.name">
                <p class="section-label mb-1">Site Name</p>
                <p class="text-[14px] font-display font-semibold text-primary">{{ result.site_info.name }}</p>
              </div>
              <div v-if="result.site_info.type">
                <p class="section-label mb-1">Type</p>
                <p class="text-[14px] text-secondary font-body capitalize">{{ result.site_info.type }}</p>
              </div>
              <div v-if="result.site_info.language">
                <p class="section-label mb-1">Language</p>
                <p class="text-[14px] text-secondary font-body">{{ result.site_info.language }}</p>
              </div>
              <div v-if="result.site_info.pages_found != null">
                <p class="section-label mb-1">Pages Found</p>
                <p class="text-[14px] text-secondary font-body">{{ result.site_info.pages_found }}</p>
              </div>
            </div>

            <!-- Status badge -->
            <div class="flex items-center gap-1.5 bg-score-good/8 border border-score-good/20 rounded-xl px-4 py-3 self-start flex-shrink-0">
              <svg class="w-4 h-4 text-score-good" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/>
              </svg>
              <span class="text-[13px] font-display font-semibold text-score-good">Generated</span>
            </div>
          </div>

          <!-- Dark code block -->
          <div class="rounded-xl overflow-hidden border border-warm-800/40 shadow-lg">
            <!-- Top bar -->
            <div class="flex items-center justify-between px-4 py-2.5 bg-[#131211] border-b border-white/5">
              <div class="flex items-center gap-2.5">
                <div class="flex gap-1.5">
                  <span class="w-3 h-3 rounded-full bg-warm-700/60"></span>
                  <span class="w-3 h-3 rounded-full bg-warm-700/60"></span>
                  <span class="w-3 h-3 rounded-full bg-warm-700/60"></span>
                </div>
                <span class="text-[12px] font-mono text-warm-500 ml-1">llms.txt</span>
              </div>
              <span class="text-[11px] text-warm-600 font-mono">plain text</span>
            </div>

            <!-- Code with line numbers -->
            <div class="bg-[#1a1917] overflow-x-auto max-h-[520px] overflow-y-auto code-scroll">
              <table class="w-full border-collapse text-[13px] font-mono leading-[1.75]">
                <tbody>
                  <tr
                    v-for="(line, i) in highlightedLines"
                    :key="i"
                    class="hover:bg-white/[0.025] transition-colors duration-75"
                  >
                    <td class="select-none text-right pr-4 pl-4 py-px text-warm-700 text-[11px] w-10 align-top border-r border-white/5 tabular-nums">
                      {{ i + 1 }}
                    </td>
                    <td class="pl-5 pr-6 py-px text-warm-300 align-top whitespace-pre-wrap break-all" v-html="line"></td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- Action buttons -->
          <div class="flex flex-wrap gap-3 mt-4">
            <button @click="copyToClipboard" class="btn-primary gap-2">
              <svg v-if="!copied" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
                <path stroke-linecap="round" d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/>
              </svg>
              <svg v-else class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/>
              </svg>
              {{ copied ? 'Copied!' : 'Copy to Clipboard' }}
            </button>
            <button @click="downloadFile" class="btn-secondary gap-2">
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/>
              </svg>
              Download llms.txt
            </button>
          </div>

        </div>
      </section>

      <!-- ─── How to Install ─── -->
      <section id="how-to-install" class="py-16 px-6 lg:px-8 border-t border-border-light">
        <div class="max-w-3xl mx-auto">
          <p class="section-label mb-3">Installation</p>
          <h2 class="font-display text-[1.7rem] font-bold text-primary mb-2">How to install your llms.txt</h2>
          <p class="text-secondary font-body mb-10">Three steps. Under two minutes.</p>

          <div class="grid sm:grid-cols-3 gap-5 stagger-children">

            <div class="bg-surface border border-border-light rounded-xl p-6 relative">
              <div class="w-8 h-8 rounded-lg bg-accent/10 flex items-center justify-center mb-4">
                <svg class="w-4 h-4 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/>
                </svg>
              </div>
              <span class="absolute top-4 right-4 text-[11px] font-display font-bold text-warm-300 tabular-nums">01</span>
              <h3 class="font-display font-semibold text-[15px] text-primary mb-1.5">Download the file</h3>
              <p class="text-[13px] text-secondary font-body leading-relaxed">Click "Download llms.txt" above to save the generated file to your computer.</p>
            </div>

            <div class="bg-surface border border-border-light rounded-xl p-6 relative">
              <div class="w-8 h-8 rounded-lg bg-accent/10 flex items-center justify-center mb-4">
                <svg class="w-4 h-4 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l4-4m0 0l4 4m-4-4v12"/>
                </svg>
              </div>
              <span class="absolute top-4 right-4 text-[11px] font-display font-bold text-warm-300 tabular-nums">02</span>
              <h3 class="font-display font-semibold text-[15px] text-primary mb-1.5">Upload to your website root</h3>
              <p class="text-[13px] text-secondary font-body leading-relaxed">Place it where your domain root resolves, so it's live at <span class="font-mono text-accent text-[12px]">yourdomain.com/llms.txt</span></p>
            </div>

            <div class="bg-surface border border-border-light rounded-xl p-6 relative">
              <div class="w-8 h-8 rounded-lg bg-accent/10 flex items-center justify-center mb-4">
                <svg class="w-4 h-4 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z"/>
                </svg>
              </div>
              <span class="absolute top-4 right-4 text-[11px] font-display font-bold text-warm-300 tabular-nums">03</span>
              <h3 class="font-display font-semibold text-[15px] text-primary mb-1.5">AI agents find you</h3>
              <p class="text-[13px] text-secondary font-body leading-relaxed">ChatGPT, Claude, Perplexity, and other AI agents can now accurately discover and describe your business.</p>
            </div>

          </div>
        </div>
      </section>

      <!-- ─── Upsell Banner ─── -->
      <section class="py-16 px-6 lg:px-8">
        <div class="max-w-3xl mx-auto">
          <div class="relative overflow-hidden rounded-2xl border border-accent/20 bg-accent/5 px-8 py-10 text-center">
            <div
              class="absolute inset-0 pointer-events-none opacity-30"
              style="background-image: linear-gradient(to right, oklch(60% 0.08 180 / 0.08) 1px, transparent 1px), linear-gradient(to bottom, oklch(60% 0.08 180 / 0.08) 1px, transparent 1px); background-size: 32px 32px;"
            ></div>
            <div class="relative">
              <p class="section-label mb-3 text-accent">Next step</p>
              <h2 class="font-display text-[1.7rem] font-bold text-primary mb-3">
                Want to check if AI agents can actually find you?
              </h2>
              <p class="text-[16px] text-secondary font-body leading-relaxed max-w-[48ch] mx-auto mb-8">
                Get your full AI readiness score with 18+ checks — protocol support, structured data, agent accessibility, trust signals, and more.
              </p>
              <router-link
                to="/"
                class="btn-primary text-[14px] px-7 py-3 inline-flex items-center gap-2"
              >
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/>
                </svg>
                Scan your website — free
              </router-link>
            </div>
          </div>
        </div>
      </section>

      <!-- ─── FAQ ─── -->
      <section id="faq" class="py-16 px-6 lg:px-8 border-t border-border-light">
        <div class="max-w-2xl mx-auto">
          <p class="section-label mb-3">FAQ</p>
          <h2 class="font-display text-[1.7rem] font-bold text-primary mb-10">Frequently asked questions</h2>

          <div class="space-y-2">
            <details
              v-for="(faq, i) in faqs"
              :key="i"
              class="group border border-border-light rounded-xl bg-surface overflow-hidden"
            >
              <summary class="flex items-center justify-between gap-4 px-5 py-4 cursor-pointer list-none font-display font-semibold text-[15px] text-primary hover:text-accent transition-colors duration-150 select-none">
                {{ faq.q }}
                <svg
                  class="w-4 h-4 text-warm-400 flex-shrink-0 transition-transform duration-200 group-open:rotate-45"
                  fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"
                >
                  <path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4"/>
                </svg>
              </summary>
              <div class="px-5 pb-5 pt-1">
                <p class="text-[14px] text-secondary font-body leading-relaxed">{{ faq.a }}</p>
              </div>
            </details>
          </div>
        </div>
      </section>

      <!-- ─── Footer ─── -->
      <footer class="border-t border-border-light py-10 px-6 lg:px-8">
        <div class="max-w-5xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4 text-[13px] text-muted font-body">
          <div class="flex items-center gap-2">
            <svg class="w-4 h-4 text-accent" viewBox="0 0 24 24" fill="none">
              <path d="M12 2L4 20h4l1.5-4h5L16 20h4L12 2zm0 7l2 5h-4l2-5z" fill="currentColor"/>
              <path d="M20 8a10 10 0 00-4-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" opacity="0.5"/>
            </svg>
            <span class="font-display font-semibold text-secondary">AgentCheck</span>
            <span class="text-warm-300">·</span>
            <span>Free AI readiness tools</span>
          </div>
          <div class="flex items-center gap-5">
            <router-link to="/" class="hover:text-primary transition-colors">Scanner</router-link>
            <router-link to="/pricing" class="hover:text-primary transition-colors">Pricing</router-link>
            <a href="https://github.com/lennystepn-hue/agentcheck" target="_blank" rel="noopener" class="hover:text-primary transition-colors">GitHub</a>
          </div>
        </div>
      </footer>

    </main>
  </div>
</template>

<style scoped>
/* Syntax highlight tokens rendered inside the dark code block */
:deep(.llms-heading) {
  color: #4dd0c4;
  font-weight: 600;
}
:deep(.llms-key) {
  color: #a8d8b9;
}
:deep(.llms-colon) {
  color: #c9c4bb;
}
:deep(.llms-url) {
  color: #7ec8e3;
  text-decoration: underline;
  text-decoration-color: rgba(126, 200, 227, 0.3);
}
:deep(.llms-comment) {
  color: #6b6860;
  font-style: italic;
}

/* Scrollbar for the code block */
.code-scroll::-webkit-scrollbar {
  height: 4px;
  width: 4px;
}
.code-scroll::-webkit-scrollbar-track {
  background: transparent;
}
.code-scroll::-webkit-scrollbar-thumb {
  background: #3a3835;
  border-radius: 2px;
}
</style>
