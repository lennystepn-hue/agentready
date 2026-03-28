<script setup>
import { isLoggedIn, user } from '../auth.js'
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
          <span class="font-display font-bold text-[15px] tracking-tight">AgentCheck</span>
        </router-link>
        <div class="flex items-center gap-6">
          <router-link to="/" class="text-[13px] text-secondary hover:text-primary transition-colors">Home</router-link>
          <router-link to="/pricing" class="text-[13px] text-secondary hover:text-primary transition-colors">Pricing</router-link>
          <template v-if="isLoggedIn">
            <router-link to="/dashboard" class="text-[13px] text-secondary hover:text-primary transition-colors">Dashboard</router-link>
            <div
              class="w-7 h-7 rounded-full bg-accent text-white flex items-center justify-center text-xs font-display font-bold"
              :title="user?.email"
            >
              {{ user?.email?.[0]?.toUpperCase() || '?' }}
            </div>
          </template>
          <router-link v-else to="/login" class="text-[13px] text-secondary hover:text-primary transition-colors">Sign in</router-link>
        </div>
      </div>
    </nav>

    <!-- Content -->
    <div class="flex-1 py-16 px-6 lg:px-8">
      <article class="max-w-prose mx-auto">
        <h1 class="font-display text-3xl font-bold tracking-tight text-primary mb-2">Impressum (Imprint)</h1>
        <p class="text-sm text-muted mb-10">Information pursuant to Section 5 TMG (German Telemedia Act)</p>

        <div class="space-y-8 text-[15px] text-secondary leading-relaxed">
          <section>
            <h2 class="font-display text-lg font-bold text-primary mb-3">Responsible person</h2>
            <p>Lenny Enderle</p>
          </section>

          <section>
            <h2 class="font-display text-lg font-bold text-primary mb-3">Contact</h2>
            <p>
              Email: <a href="mailto:contact@agentcheck.site" class="text-accent hover:text-accent-hover transition-colors font-medium">contact@agentcheck.site</a>
            </p>
          </section>

          <section>
            <h2 class="font-display text-lg font-bold text-primary mb-3">Responsible for content</h2>
            <p>Lenny Enderle</p>
            <p class="mt-2 text-sm text-muted">Responsible for content pursuant to Section 55(2) RStV (German Interstate Broadcasting Treaty).</p>
          </section>

          <section>
            <h2 class="font-display text-lg font-bold text-primary mb-3">Dispute resolution</h2>
            <p>The European Commission provides a platform for online dispute resolution (OS): <a href="https://ec.europa.eu/consumers/odr/" target="_blank" rel="noopener" class="text-accent hover:text-accent-hover transition-colors">https://ec.europa.eu/consumers/odr/</a></p>
            <p class="mt-2">We are not willing or obliged to participate in dispute resolution proceedings before a consumer arbitration board.</p>
          </section>
        </div>
      </article>
    </div>

    <!-- Footer -->
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
