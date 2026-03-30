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
        <h1 class="font-display text-3xl font-bold tracking-tight text-primary mb-2">Terms of Service</h1>
        <p class="text-sm text-muted mb-10">Last updated: March 2026</p>

        <!-- Table of Contents -->
        <nav class="mb-10 p-5 bg-warm-50 border border-border-light rounded-lg">
          <p class="text-xs font-display font-semibold text-muted uppercase tracking-wider mb-3">Table of Contents</p>
          <ol class="list-decimal list-inside space-y-1.5 text-sm text-secondary">
            <li><a href="#service-description" class="hover:text-accent transition-colors">Service description</a></li>
            <li><a href="#account-terms" class="hover:text-accent transition-colors">Account terms</a></li>
            <li><a href="#payment-terms" class="hover:text-accent transition-colors">Payment terms</a></li>
            <li><a href="#acceptable-use" class="hover:text-accent transition-colors">Acceptable use</a></li>
            <li><a href="#disclaimer" class="hover:text-accent transition-colors">Disclaimer</a></li>
            <li><a href="#liability" class="hover:text-accent transition-colors">Limitation of liability</a></li>
            <li><a href="#changes" class="hover:text-accent transition-colors">Changes to terms</a></li>
            <li><a href="#governing-law" class="hover:text-accent transition-colors">Governing law</a></li>
            <li><a href="#contact" class="hover:text-accent transition-colors">Contact</a></li>
          </ol>
        </nav>

        <div class="space-y-8 text-[15px] text-secondary leading-relaxed">
          <section id="service-description">
            <h2 class="font-display text-lg font-bold text-primary mb-3">1. Service description</h2>
            <p>AgentCheck is an AI readiness scanning tool for e-commerce websites. It analyzes publicly accessible web pages to evaluate how discoverable and interactable they are for AI shopping agents. The service provides scores, grades, and actionable recommendations to improve AI agent compatibility.</p>
          </section>

          <section id="account-terms">
            <h2 class="font-display text-lg font-bold text-primary mb-3">2. Account terms</h2>
            <ul class="list-disc list-inside space-y-1.5 ml-2">
              <li>You must be at least 18 years old to create an account and use our paid services.</li>
              <li>You must provide accurate and complete information when creating your account.</li>
              <li>You are responsible for maintaining the security of your account credentials.</li>
              <li>You may not use another person's account without their permission.</li>
              <li>We reserve the right to suspend or terminate accounts that violate these terms.</li>
            </ul>
          </section>

          <section id="payment-terms">
            <h2 class="font-display text-lg font-bold text-primary mb-3">3. Payment terms</h2>
            <p class="mb-3">AgentCheck offers the following paid plans:</p>
            <ul class="list-disc list-inside space-y-1.5 ml-2">
              <li><strong class="text-primary">Fix Files</strong> -- $9 one-time payment per scan. Includes tailored ai.txt, llms.txt, Schema markup, and other fix files customized for your scan results.</li>
              <li><strong class="text-primary">Pro</strong> -- $29/month subscription. Includes weekly monitoring, competitor comparison, score history, unlimited fix files, and AI bot traffic tracking.</li>
            </ul>
            <p class="mt-3">All payments are processed securely through Stripe. Pro subscriptions can be cancelled at any time through the Stripe billing portal. Cancellation takes effect at the end of the current billing period. We do not offer refunds for partial billing periods.</p>
          </section>

          <section id="acceptable-use">
            <h2 class="font-display text-lg font-bold text-primary mb-3">4. Acceptable use</h2>
            <p class="mb-3">You agree not to:</p>
            <ul class="list-disc list-inside space-y-1.5 ml-2">
              <li>Abuse the scanning service by sending excessive or automated requests beyond normal usage.</li>
              <li>Attempt to circumvent rate limits or other technical restrictions.</li>
              <li>Use the service to scan websites you do not own or have authorization to test.</li>
              <li>Interfere with or disrupt the service or its infrastructure.</li>
              <li>Use the service for any unlawful purpose.</li>
            </ul>
            <p class="mt-3">Rate limits apply to all accounts. Free accounts are subject to stricter rate limits than paid accounts.</p>
          </section>

          <section id="disclaimer">
            <h2 class="font-display text-lg font-bold text-primary mb-3">5. Disclaimer</h2>
            <p class="mb-3">AgentCheck scores and recommendations are provided for informational purposes only. While we strive to provide accurate and useful assessments:</p>
            <ul class="list-disc list-inside space-y-1.5 ml-2">
              <li>Scores are not guaranteed to improve your search rankings or AI agent visibility.</li>
              <li>Recommendations are based on current best practices, which may change as AI commerce standards evolve.</li>
              <li>We do not guarantee that implementing our recommendations will result in specific business outcomes.</li>
            </ul>
            <p class="mt-3">The service is provided "as is" and "as available" without warranties of any kind, either express or implied.</p>
          </section>

          <section id="liability">
            <h2 class="font-display text-lg font-bold text-primary mb-3">6. Limitation of liability</h2>
            <p>To the maximum extent permitted by applicable law, AgentCheck and its operators shall not be liable for any indirect, incidental, special, consequential, or punitive damages, or any loss of profits or revenue, whether incurred directly or indirectly, or any loss of data, use, goodwill, or other intangible losses resulting from your use of the service.</p>
          </section>

          <section id="changes">
            <h2 class="font-display text-lg font-bold text-primary mb-3">7. Changes to terms</h2>
            <p>We may update these terms from time to time. If we make material changes, we will notify registered users by email. Continued use of the service after changes take effect constitutes acceptance of the updated terms.</p>
          </section>

          <section id="governing-law">
            <h2 class="font-display text-lg font-bold text-primary mb-3">8. Governing law</h2>
            <p>These terms are governed by and construed in accordance with the laws of Germany and the European Union. Any disputes arising from these terms or your use of the service shall be subject to the exclusive jurisdiction of the courts in Germany.</p>
          </section>

          <section id="contact">
            <h2 class="font-display text-lg font-bold text-primary mb-3">9. Contact</h2>
            <p>For questions about these terms, please contact us at:</p>
            <p class="mt-2">
              <a href="mailto:legal@agentcheck.site" class="text-accent hover:text-accent-hover transition-colors font-medium">legal@agentcheck.site</a>
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
