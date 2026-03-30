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
        <h1 class="font-display text-3xl font-bold tracking-tight text-primary mb-2">Privacy Policy</h1>
        <p class="text-sm text-muted mb-10">Last updated: March 2026</p>

        <!-- Table of Contents -->
        <nav class="mb-10 p-5 bg-warm-50 border border-border-light rounded-lg">
          <p class="text-xs font-display font-semibold text-muted uppercase tracking-wider mb-3">Table of Contents</p>
          <ol class="list-decimal list-inside space-y-1.5 text-sm text-secondary">
            <li><a href="#data-we-collect" class="hover:text-accent transition-colors">What data we collect</a></li>
            <li><a href="#how-we-use-it" class="hover:text-accent transition-colors">How we use it</a></li>
            <li><a href="#third-parties" class="hover:text-accent transition-colors">Third parties</a></li>
            <li><a href="#data-retention" class="hover:text-accent transition-colors">Data retention</a></li>
            <li><a href="#gdpr-rights" class="hover:text-accent transition-colors">Your rights (GDPR)</a></li>
            <li><a href="#contact" class="hover:text-accent transition-colors">Contact</a></li>
          </ol>
        </nav>

        <div class="space-y-8 text-[15px] text-secondary leading-relaxed">
          <section id="data-we-collect">
            <h2 class="font-display text-lg font-bold text-primary mb-3">1. What data we collect</h2>
            <p class="mb-3">When you use AgentCheck, we may collect the following information:</p>
            <ul class="list-disc list-inside space-y-1.5 ml-2">
              <li><strong class="text-primary">Email address</strong> -- when you create an account or opt in to notifications.</li>
              <li><strong class="text-primary">Scan results</strong> -- the domains you scan and the resulting scores, checks, and fix recommendations.</li>
              <li><strong class="text-primary">IP address</strong> -- used solely for rate limiting and abuse prevention. We do not use IP addresses for tracking or profiling.</li>
            </ul>
          </section>

          <section id="how-we-use-it">
            <h2 class="font-display text-lg font-bold text-primary mb-3">2. How we use it</h2>
            <p>We use the data we collect to:</p>
            <ul class="list-disc list-inside space-y-1.5 ml-2 mt-3">
              <li>Provide the AgentCheck scanning service and display your reports.</li>
              <li>Send you email notifications about scan results and score changes, if you have opted in.</li>
              <li>Enforce rate limits and prevent abuse of the service.</li>
              <li>Improve the accuracy and performance of our scanning tool.</li>
            </ul>
          </section>

          <section id="third-parties">
            <h2 class="font-display text-lg font-bold text-primary mb-3">3. Third parties</h2>
            <p class="mb-3">We use <strong class="text-primary">Stripe</strong> to process payments. When you purchase Fix Files or subscribe to Pro, your payment information is handled directly by Stripe. We do not store your credit card details.</p>
            <p>We do not sell, rent, or share your personal data with any other third parties.</p>
          </section>

          <section id="data-retention">
            <h2 class="font-display text-lg font-bold text-primary mb-3">4. Data retention</h2>
            <p class="mb-3">Scan results are stored so you can access your reports and track score changes over time. You may request deletion of your scan data and account at any time by contacting us.</p>
            <p>If you delete your account, all associated scan data will be permanently removed within 30 days.</p>
          </section>

          <section id="gdpr-rights">
            <h2 class="font-display text-lg font-bold text-primary mb-3">5. Your rights (GDPR)</h2>
            <p class="mb-3">If you are located in the European Union, you have the following rights under the General Data Protection Regulation (GDPR):</p>
            <ul class="list-disc list-inside space-y-1.5 ml-2">
              <li><strong class="text-primary">Right of access</strong> -- you can request a copy of all personal data we hold about you.</li>
              <li><strong class="text-primary">Right to deletion</strong> -- you can request that we delete your personal data and account.</li>
              <li><strong class="text-primary">Right to data portability</strong> -- you can request your data in a structured, machine-readable format.</li>
              <li><strong class="text-primary">Right to rectification</strong> -- you can request correction of inaccurate data.</li>
              <li><strong class="text-primary">Right to object</strong> -- you can object to the processing of your personal data.</li>
            </ul>
            <p class="mt-3">To exercise any of these rights, please contact us at the address below.</p>
          </section>

          <section id="contact">
            <h2 class="font-display text-lg font-bold text-primary mb-3">6. Contact</h2>
            <p>For privacy-related inquiries, please contact us at:</p>
            <p class="mt-2">
              <a href="mailto:privacy@agentcheck.site" class="text-accent hover:text-accent-hover transition-colors font-medium">privacy@agentcheck.site</a>
            </p>
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
