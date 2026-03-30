<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { initAuth, isLoggedIn, user } from '../auth.js'
import AppHeader from '../components/AppHeader.vue'

const route = useRoute()

const type = computed(() => route.query.type || 'pro')
const scanId = computed(() => route.query.scan_id || '')
const itemsVisible = ref(false)

onMounted(async () => {
  // Refresh user data to pick up new plan or purchase
  await initAuth()
  // Stagger the unlock list in after the check icon settles
  setTimeout(() => { itemsVisible.value = true }, 500)
})

const proUnlocks = [
  {
    icon: `<path stroke-linecap="round" stroke-linejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>`,
    label: 'Score history & trend tracking',
  },
  {
    icon: `<path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>`,
    label: 'Unlimited fix file downloads',
  },
  {
    icon: `<path stroke-linecap="round" stroke-linejoin="round" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"/>`,
    label: 'Competitor comparison (up to 3 domains)',
  },
  {
    icon: `<path stroke-linecap="round" stroke-linejoin="round" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"/>`,
    label: 'Automated re-scan monitoring',
  },
]

const fixFilesUnlocks = [
  {
    icon: `<path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>`,
    label: 'llms.txt — AI agent discovery file',
  },
  {
    icon: `<path stroke-linecap="round" stroke-linejoin="round" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"/>`,
    label: 'ai.txt — Structured AI permissions',
  },
  {
    icon: `<path stroke-linecap="round" stroke-linejoin="round" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"/>`,
    label: 'Schema.org JSON-LD patches',
  },
  {
    icon: `<path stroke-linecap="round" stroke-linejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>`,
    label: 'robots.txt AI-agent rules block',
  },
]

const unlocks = computed(() => type.value === 'fix_files' ? fixFilesUnlocks : proUnlocks)
</script>

<template>
  <div class="flex-1 flex flex-col">
    <AppHeader />

    <!-- Content -->
    <div class="flex-1 flex items-start justify-center px-6 lg:px-8 py-16 sm:py-24">
      <div class="w-full max-w-md">

        <!-- Radial burst + check icon -->
        <div class="relative flex items-center justify-center mb-8">
          <!-- CSS particle burst (pure SVG rings) -->
          <div class="absolute inset-0 flex items-center justify-center pointer-events-none" aria-hidden="true">
            <div class="burst-ring burst-ring-1"></div>
            <div class="burst-ring burst-ring-2"></div>
            <div class="burst-ring burst-ring-3"></div>
          </div>

          <!-- Confetti dots -->
          <div class="absolute inset-0 flex items-center justify-center pointer-events-none" aria-hidden="true">
            <span class="confetti-dot" style="--x: -52px; --y: -38px; --delay: 0ms; --color: #0D7377;"></span>
            <span class="confetti-dot" style="--x: 44px; --y: -52px; --delay: 60ms; --color: #3D8B5E;"></span>
            <span class="confetti-dot" style="--x: 58px; --y: 16px; --delay: 120ms; --color: #C08832;"></span>
            <span class="confetti-dot" style="--x: 28px; --y: 52px; --delay: 80ms; --color: #0D7377;"></span>
            <span class="confetti-dot" style="--x: -38px; --y: 48px; --delay: 40ms; --color: #3D8B5E;"></span>
            <span class="confetti-dot" style="--x: -58px; --y: 10px; --delay: 100ms; --color: #C08832;"></span>
            <span class="confetti-dot confetti-dot--sm" style="--x: -24px; --y: -60px; --delay: 30ms; --color: #0D7377;"></span>
            <span class="confetti-dot confetti-dot--sm" style="--x: 62px; --y: -30px; --delay: 90ms; --color: #3D8B5E;"></span>
          </div>

          <!-- Check icon -->
          <div class="relative z-10 w-16 h-16 rounded-full bg-score-good/12 border border-score-good/20 flex items-center justify-center check-bounce">
            <svg class="w-8 h-8 text-score-good" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
            </svg>
          </div>
        </div>

        <!-- Heading block -->
        <div class="text-center mb-8 animate-fade-in">
          <h1 class="font-display text-2xl font-bold tracking-tight text-primary mb-2">
            {{ type === 'fix_files' ? 'Your fix files are ready' : 'Pro is active' }}
          </h1>
          <p class="text-secondary text-sm leading-relaxed max-w-xs mx-auto">
            <template v-if="type === 'fix_files'">
              Your ready-to-deploy fix files have been generated. Head to your report to download them.
            </template>
            <template v-else>
              Your Pro plan is live. You now have full access to monitoring, history, competitor comparison, and unlimited fix files.
            </template>
          </p>
        </div>

        <!-- What's unlocked -->
        <div class="mb-8">
          <p class="section-label mb-4 text-center">
            {{ type === 'fix_files' ? 'Files generated' : 'Now unlocked' }}
          </p>

          <div class="space-y-2">
            <div
              v-for="(item, i) in unlocks"
              :key="i"
              class="flex items-center gap-3 px-4 py-3 bg-surface rounded-lg border border-border-light transition-opacity duration-300"
              :class="itemsVisible ? 'unlock-item-visible' : 'opacity-0'"
              :style="{ animationDelay: `${i * 80}ms` }"
            >
              <div class="flex-shrink-0 w-8 h-8 rounded-md bg-accent/10 flex items-center justify-center">
                <svg class="w-4 h-4 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.7" v-html="item.icon" />
              </div>
              <span class="text-sm font-display font-medium text-primary">{{ item.label }}</span>
              <svg class="w-4 h-4 text-score-good ml-auto flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
              </svg>
            </div>
          </div>
        </div>

        <!-- Fix files: mini generation progress -->
        <div v-if="type === 'fix_files'" class="mb-8 p-4 bg-warm-50 rounded-xl border border-border-light animate-fade-in">
          <div class="flex items-center justify-between mb-2.5">
            <span class="text-[13px] font-display font-semibold text-primary">Generating fix files</span>
            <span class="text-xs text-score-good font-display font-semibold">Complete</span>
          </div>
          <div class="h-1.5 bg-warm-200 rounded-full overflow-hidden">
            <div class="h-full bg-score-good rounded-full transition-all duration-1000" style="width: 100%"></div>
          </div>
          <p class="text-xs text-muted mt-2">All 4 files are attached to your report.</p>
        </div>

        <!-- Next step callout -->
        <div class="mb-8 p-4 bg-accent/5 border border-accent/15 rounded-xl animate-slide-up">
          <p class="text-xs font-display font-semibold text-accent uppercase tracking-wider mb-1">Next step</p>
          <p class="text-sm text-primary font-medium" v-if="type === 'fix_files' && scanId">
            Go to your report and download your fix files to deploy them.
          </p>
          <p class="text-sm text-primary font-medium" v-else-if="type === 'fix_files'">
            Open your report to download the fix files and see detailed instructions.
          </p>
          <p class="text-sm text-primary font-medium" v-else>
            Run your first AI Discovery Test to see your full readiness breakdown.
          </p>
        </div>

        <!-- CTAs -->
        <div class="flex flex-col sm:flex-row gap-3">
          <router-link
            v-if="type === 'fix_files' && scanId"
            :to="{ name: 'Report', params: { id: scanId } }"
            class="btn-primary flex-1 justify-center"
          >
            Go to report &amp; download
          </router-link>
          <router-link
            v-else-if="type === 'fix_files'"
            to="/dashboard"
            class="btn-primary flex-1 justify-center"
          >
            Go to dashboard
          </router-link>
          <template v-else>
            <router-link to="/" class="btn-primary flex-1 justify-center">
              Run a scan
            </router-link>
            <router-link to="/dashboard" class="btn-secondary flex-1 justify-center">
              Go to dashboard
            </router-link>
          </template>
        </div>

      </div>
    </div>

    <!-- Footer -->
    <footer class="border-t border-border-light py-5 px-6 lg:px-8 mt-auto">
      <div class="max-w-5xl mx-auto flex items-center justify-between">
        <span class="text-xs text-muted">&copy; {{ new Date().getFullYear() }} AgentCheck</span>
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
        </div>
      </div>
    </footer>
  </div>
</template>

<style scoped>
/* Check icon bounce-in */
.check-bounce {
  animation: checkBounce 0.55s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
}

@keyframes checkBounce {
  0%   { transform: scale(0.3); opacity: 0; }
  60%  { transform: scale(1.08); opacity: 1; }
  100% { transform: scale(1); opacity: 1; }
}

/* Radial burst rings */
.burst-ring {
  position: absolute;
  border-radius: 50%;
  border: 1.5px solid;
  animation: burstExpand 0.7s cubic-bezier(0.25, 0.46, 0.45, 0.94) forwards;
  opacity: 0;
}

.burst-ring-1 {
  width: 80px;
  height: 80px;
  border-color: rgba(13, 115, 119, 0.35);
  animation-delay: 100ms;
}

.burst-ring-2 {
  width: 110px;
  height: 110px;
  border-color: rgba(13, 115, 119, 0.22);
  animation-delay: 180ms;
}

.burst-ring-3 {
  width: 144px;
  height: 144px;
  border-color: rgba(13, 115, 119, 0.12);
  animation-delay: 260ms;
}

@keyframes burstExpand {
  0%   { transform: scale(0.5); opacity: 0.8; }
  100% { transform: scale(1); opacity: 0; }
}

/* Confetti dots */
.confetti-dot {
  position: absolute;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background-color: var(--color);
  animation: confettiPop 0.55s cubic-bezier(0.34, 1.56, 0.64, 1) var(--delay, 0ms) both;
  transform: translate(0, 0) scale(0);
}

.confetti-dot--sm {
  width: 4px;
  height: 4px;
}

@keyframes confettiPop {
  0%   { transform: translate(0, 0) scale(0); opacity: 1; }
  60%  { transform: translate(var(--x), var(--y)) scale(1); opacity: 1; }
  100% { transform: translate(var(--x), var(--y)) scale(0.6); opacity: 0; }
}

/* Unlock list item stagger-in */
.unlock-item-visible {
  animation: unlockSlideIn 0.35s ease-out both;
}

@keyframes unlockSlideIn {
  from { opacity: 0; transform: translateX(-8px); }
  to   { opacity: 1; transform: translateX(0); }
}
</style>
