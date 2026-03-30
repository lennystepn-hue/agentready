# AgentCheck UX Overhaul Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform AgentCheck from "a scanner tool" into "the service that gets your website recommended by AI agents" — with a polished, user-friendly interface that drives Pro conversions.

**Architecture:** Three parallel workstreams: (1) Header/Profile UX — clickable avatar dropdown, unified nav across all pages, (2) Dashboard redesign — action-oriented layout with clear upgrade path, (3) Sales messaging shift — "we get you found" not "we scan you". All changes are frontend-only except minor backend additions for user profile.

**Tech Stack:** Vue 3 (Composition API), Tailwind CSS, existing auth.js store, existing API endpoints.

---

## File Map

| File | Action | Responsibility |
|------|--------|---------------|
| `frontend/src/components/UserDropdown.vue` | CREATE | Clickable avatar with dropdown menu (profile, plan, billing, sign out) |
| `frontend/src/components/AppHeader.vue` | CREATE | Unified header component used across ALL pages (landing, report, dashboard, pricing) |
| `frontend/src/components/UpgradeCard.vue` | CREATE | Reusable Pro upgrade CTA component with consistent messaging |
| `frontend/src/components/AppLayout.vue` | MODIFY | Use new AppHeader, fix sidebar, improve mobile nav |
| `frontend/src/pages/Dashboard.vue` | MODIFY | Full redesign: hero stats, recent scans, AI visibility score, upgrade flow |
| `frontend/src/pages/Landing.vue` | MODIFY | New nav via AppHeader, shift sales messaging to "get found by AI" |
| `frontend/src/pages/Report.vue` | MODIFY | New nav via AppHeader, consistent with other pages |
| `frontend/src/pages/Pricing.vue` | MODIFY | Shift messaging: "Boost your AI visibility" not "Paid fixes" |
| `frontend/src/pages/ScanProgress.vue` | MODIFY | Use AppHeader |
| `frontend/src/pages/Badge.vue` | MODIFY | Use AppHeader |
| `frontend/src/pages/Login.vue` | MODIFY | Use AppHeader |

---

## Task 1: Create UserDropdown Component

**Files:**
- Create: `frontend/src/components/UserDropdown.vue`

The avatar in the top-right is currently just a static circle with no click behavior. This creates a proper dropdown menu.

- [ ] **Step 1: Create UserDropdown.vue**

```vue
<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { user, isPro, logout } from '../auth.js'
import { createBillingPortal } from '../api.js'

const router = useRouter()
const open = ref(false)
const managingBilling = ref(false)

function toggleDropdown() {
  open.value = !open.value
}

function closeDropdown() {
  open.value = false
}

async function handleManageSubscription() {
  managingBilling.value = true
  try {
    const data = await createBillingPortal()
    if (data.portal_url) window.location.href = data.portal_url
  } catch {
    // silent fail
  } finally {
    managingBilling.value = false
  }
}

function handleLogout() {
  logout()
  router.push('/')
  open.value = false
}
</script>

<template>
  <div class="relative">
    <!-- Avatar trigger -->
    <button
      @click="toggleDropdown"
      class="flex items-center gap-2 rounded-full focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-page"
    >
      <div class="w-8 h-8 rounded-full bg-accent text-white flex items-center justify-center text-xs font-display font-bold cursor-pointer hover:ring-2 hover:ring-accent/30 transition-all">
        {{ user?.email?.[0]?.toUpperCase() || '?' }}
      </div>
    </button>

    <!-- Dropdown -->
    <Transition
      enter-active-class="transition ease-out duration-150"
      enter-from-class="opacity-0 translate-y-1"
      enter-to-class="opacity-100 translate-y-0"
      leave-active-class="transition ease-in duration-100"
      leave-from-class="opacity-100 translate-y-0"
      leave-to-class="opacity-0 translate-y-1"
    >
      <div
        v-if="open"
        class="absolute right-0 mt-2 w-64 bg-surface border border-border rounded-lg shadow-lg overflow-hidden z-50"
        @click.stop
      >
        <!-- User info -->
        <div class="px-4 py-3 border-b border-border-light">
          <p class="text-sm font-display font-semibold text-primary truncate">{{ user?.email }}</p>
          <div class="flex items-center gap-2 mt-1">
            <span
              class="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-display font-bold uppercase tracking-wider"
              :class="isPro ? 'bg-accent text-white' : 'bg-warm-200 text-warm-600'"
            >
              {{ isPro ? 'Pro' : 'Free' }}
            </span>
            <span v-if="isPro" class="text-[11px] text-accent">$29/mo</span>
          </div>
        </div>

        <!-- Menu items -->
        <div class="py-1">
          <router-link
            to="/dashboard"
            @click="closeDropdown"
            class="flex items-center gap-2.5 px-4 py-2 text-sm text-secondary hover:bg-warm-50 hover:text-primary transition-colors"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zm10 0a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zm10 0a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
            </svg>
            Dashboard
          </router-link>

          <router-link
            to="/pricing"
            @click="closeDropdown"
            class="flex items-center gap-2.5 px-4 py-2 text-sm text-secondary hover:bg-warm-50 hover:text-primary transition-colors"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
            </svg>
            {{ isPro ? 'Your plan' : 'Upgrade to Pro' }}
          </router-link>

          <button
            v-if="isPro"
            @click="handleManageSubscription"
            :disabled="managingBilling"
            class="w-full flex items-center gap-2.5 px-4 py-2 text-sm text-secondary hover:bg-warm-50 hover:text-primary transition-colors text-left"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
            </svg>
            {{ managingBilling ? 'Loading...' : 'Manage billing' }}
          </button>
        </div>

        <!-- Sign out -->
        <div class="border-t border-border-light py-1">
          <button
            @click="handleLogout"
            class="w-full flex items-center gap-2.5 px-4 py-2 text-sm text-secondary hover:bg-warm-50 hover:text-primary transition-colors text-left"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
            Sign out
          </button>
        </div>
      </div>
    </Transition>

    <!-- Click outside to close -->
    <div v-if="open" class="fixed inset-0 z-40" @click="closeDropdown" />
  </div>
</template>
```

- [ ] **Step 2: Verify file created correctly**

Run: `cat frontend/src/components/UserDropdown.vue | head -5`
Expected: `<script setup>` on first line

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/UserDropdown.vue
git commit -m "feat: add UserDropdown component with profile menu, billing, sign out"
```

---

## Task 2: Create Unified AppHeader Component

**Files:**
- Create: `frontend/src/components/AppHeader.vue`

Currently every page has its own copy-pasted nav. This creates ONE header used everywhere — adapts based on auth state, current route, and page context.

- [ ] **Step 1: Create AppHeader.vue**

```vue
<script setup>
import { isLoggedIn, user } from '../auth.js'
import UserDropdown from './UserDropdown.vue'

defineProps({
  transparent: { type: Boolean, default: false },
  showBack: { type: String, default: '' }, // route path for back button, empty = no back
  backLabel: { type: String, default: 'Back' },
})
</script>

<template>
  <nav
    class="sticky top-0 z-50 border-b transition-colors"
    :class="transparent ? 'bg-transparent border-transparent' : 'bg-page/95 backdrop-blur-sm border-border-light'"
  >
    <div class="max-w-5xl mx-auto px-6 lg:px-8 h-14 flex items-center justify-between">
      <!-- Left: Logo + optional back button -->
      <div class="flex items-center gap-4">
        <router-link to="/" class="flex items-center gap-2">
          <svg class="w-5 h-5 text-accent" viewBox="0 0 24 24" fill="none">
            <path d="M12 2L4 20h4l1.5-4h5L16 20h4L12 2zm0 7l2 5h-4l2-5z" fill="currentColor"/>
            <path d="M20 8a10 10 0 00-4-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" opacity="0.5"/>
            <path d="M22 6a14 14 0 00-6-5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" opacity="0.3"/>
          </svg>
          <span class="font-display font-bold text-[15px] tracking-tight">AgentCheck</span>
        </router-link>

        <!-- Back button -->
        <router-link
          v-if="showBack"
          :to="showBack"
          class="hidden sm:flex items-center gap-1 text-[13px] text-secondary hover:text-primary transition-colors"
        >
          <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
          </svg>
          {{ backLabel }}
        </router-link>
      </div>

      <!-- Right: nav links + auth -->
      <div class="flex items-center gap-5">
        <!-- Extra slot for page-specific actions -->
        <slot name="actions" />

        <!-- Standard nav links (hidden on mobile for authenticated pages) -->
        <router-link
          to="/pricing"
          class="hidden sm:block text-[13px] text-secondary hover:text-primary transition-colors"
          :class="{ 'text-accent font-medium': $route.path === '/pricing' }"
        >
          Pricing
        </router-link>

        <a
          href="https://github.com/lennystepn-hue/agentcheck"
          target="_blank"
          rel="noopener"
          class="hidden sm:block text-secondary hover:text-primary transition-colors"
          aria-label="GitHub"
        >
          <svg class="w-[18px] h-[18px]" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z" />
          </svg>
        </a>

        <!-- Auth state -->
        <template v-if="isLoggedIn">
          <UserDropdown />
        </template>
        <router-link
          v-else
          to="/login"
          class="text-[13px] font-display font-medium text-accent hover:text-accent-hover transition-colors"
        >
          Sign in
        </router-link>
      </div>
    </div>
  </nav>
</template>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/AppHeader.vue
git commit -m "feat: add unified AppHeader with UserDropdown, used across all pages"
```

---

## Task 3: Create Reusable UpgradeCard Component

**Files:**
- Create: `frontend/src/components/UpgradeCard.vue`

Consistent Pro upgrade CTA used in dashboard, report, and feature pages. Shifts messaging to "get found by AI".

- [ ] **Step 1: Create UpgradeCard.vue**

```vue
<script setup>
import { ref } from 'vue'
import { createCheckoutSession } from '../api.js'

defineProps({
  compact: { type: Boolean, default: false },
  context: { type: String, default: '' }, // "dashboard", "report", "feature"
})

const upgrading = ref(false)
const error = ref('')

async function handleUpgrade() {
  upgrading.value = true
  error.value = ''
  try {
    const session = await createCheckoutSession('pro', null)
    const url = session.checkout_url || session.url
    if (url) window.location.href = url
  } catch (e) {
    error.value = e.message || 'Could not start checkout.'
  } finally {
    upgrading.value = false
  }
}
</script>

<template>
  <!-- Compact version for inline use -->
  <div v-if="compact" class="flex items-center justify-between gap-4 border border-accent/20 rounded-lg px-4 py-3 bg-accent/[0.03]">
    <div class="min-w-0">
      <p class="text-sm font-display font-semibold text-primary">Get found by AI agents</p>
      <p class="text-xs text-secondary mt-0.5">Pro unlocks monitoring, discovery tests, and competitor insights.</p>
    </div>
    <button @click="handleUpgrade" :disabled="upgrading" class="btn-primary text-xs px-4 py-1.5 flex-shrink-0">
      {{ upgrading ? '...' : 'Upgrade — $29/mo' }}
    </button>
  </div>

  <!-- Full version for sections -->
  <div v-else class="border border-accent/20 rounded-lg overflow-hidden">
    <div class="bg-accent/[0.04] px-6 py-8">
      <div class="max-w-lg">
        <p class="text-[11px] font-display font-semibold text-accent uppercase tracking-widest mb-3">Pro Plan</p>
        <h3 class="font-display text-xl font-bold text-primary mb-2">
          Make AI agents recommend your site
        </h3>
        <p class="text-sm text-secondary leading-relaxed mb-1">
          We don't just tell you what's wrong — we help you fix it, monitor your progress, and verify that AI agents actually find you.
        </p>
        <ul class="mt-4 space-y-2">
          <li class="flex items-center gap-2 text-sm text-secondary">
            <svg class="w-4 h-4 text-accent flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" /></svg>
            Unlimited tailored fix files
          </li>
          <li class="flex items-center gap-2 text-sm text-secondary">
            <svg class="w-4 h-4 text-accent flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" /></svg>
            Weekly monitoring + score alerts
          </li>
          <li class="flex items-center gap-2 text-sm text-secondary">
            <svg class="w-4 h-4 text-accent flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" /></svg>
            AI Discovery Test — see if ChatGPT/Claude find you
          </li>
          <li class="flex items-center gap-2 text-sm text-secondary">
            <svg class="w-4 h-4 text-accent flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" /></svg>
            AI-powered competitor analysis
          </li>
          <li class="flex items-center gap-2 text-sm text-secondary">
            <svg class="w-4 h-4 text-accent flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" /></svg>
            Score history over time
          </li>
        </ul>
        <div class="mt-6 flex items-center gap-4">
          <button @click="handleUpgrade" :disabled="upgrading" class="btn-primary">
            {{ upgrading ? 'Starting...' : 'Start Pro — $29/mo' }}
          </button>
          <span class="text-xs text-muted">Cancel anytime</span>
        </div>
        <p v-if="error" class="mt-2 text-xs text-score-bad">{{ error }}</p>
      </div>
    </div>
  </div>
</template>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/UpgradeCard.vue
git commit -m "feat: add reusable UpgradeCard with 'get found by AI' messaging"
```

---

## Task 4: Integrate AppHeader into Landing.vue

**Files:**
- Modify: `frontend/src/pages/Landing.vue` (nav section only)

Replace the duplicated nav in Landing.vue with AppHeader. Keep all Landing-specific content (hero, sections, footer) intact.

- [ ] **Step 1: Replace Landing.vue nav with AppHeader**

In the `<script setup>` block, add:
```javascript
import AppHeader from '../components/AppHeader.vue'
```

Replace the entire `<!-- ─── Nav ─── -->` section (the `<nav>...</nav>` block) with:
```html
<AppHeader>
  <template #actions>
    <a href="#how-it-works" class="hidden sm:block text-[13px] text-secondary hover:text-primary transition-colors">How it works</a>
    <a href="#checks" class="hidden sm:block text-[13px] text-secondary hover:text-primary transition-colors">Checks</a>
    <a href="#faq" class="hidden sm:block text-[13px] text-secondary hover:text-primary transition-colors">FAQ</a>
  </template>
</AppHeader>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/Landing.vue
git commit -m "refactor: use AppHeader in Landing.vue"
```

---

## Task 5: Integrate AppHeader into Report, Pricing, ScanProgress, Badge, Login

**Files:**
- Modify: `frontend/src/pages/Report.vue` (nav section)
- Modify: `frontend/src/pages/Pricing.vue` (nav section)
- Modify: `frontend/src/pages/ScanProgress.vue` (nav section)
- Modify: `frontend/src/pages/Badge.vue` (nav section)
- Modify: `frontend/src/pages/Login.vue` (nav section)

Each page: import AppHeader, replace existing nav, configure props (showBack, backLabel, etc).

- [ ] **Step 1: Update Report.vue**

Import AppHeader, replace nav with:
```html
<AppHeader :show-back="isLoggedIn ? '/dashboard' : '/'" :back-label="isLoggedIn ? 'Dashboard' : 'Home'">
  <template #actions>
    <button @click="shareReport" class="text-[13px] text-secondary hover:text-primary transition-colors flex items-center gap-1">
      <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
      </svg>
      {{ copied ? 'Copied!' : 'Share' }}
    </button>
  </template>
</AppHeader>
```

Remove the old `import { logout } from '../auth.js'` if no longer used elsewhere in Report.vue.

- [ ] **Step 2: Update Pricing.vue** — replace nav with `<AppHeader />`

- [ ] **Step 3: Update ScanProgress.vue** — replace nav with `<AppHeader show-back="/" back-label="Home" />`

- [ ] **Step 4: Update Badge.vue** — replace nav with:
```html
<AppHeader :show-back="'/report/' + scanId" back-label="Report" />
```

- [ ] **Step 5: Update Login.vue** — replace nav with `<AppHeader show-back="/" back-label="Home" />`

- [ ] **Step 6: Commit**

```bash
git add frontend/src/pages/Report.vue frontend/src/pages/Pricing.vue frontend/src/pages/ScanProgress.vue frontend/src/pages/Badge.vue frontend/src/pages/Login.vue
git commit -m "refactor: use unified AppHeader across all pages"
```

---

## Task 6: Update AppLayout Sidebar + Use AppHeader

**Files:**
- Modify: `frontend/src/components/AppLayout.vue`

Replace the duplicated nav in AppLayout with AppHeader. Simplify sidebar. Fix mobile nav.

- [ ] **Step 1: Rewrite AppLayout to use AppHeader**

Replace the top nav section with `<AppHeader />`. The sidebar stays but gets cleaned up — remove redundant user info (now in UserDropdown). Mobile bottom nav keeps its icons but links to correct routes.

Key changes:
- Top nav → `<AppHeader />`
- Remove sign-out from sidebar (now in UserDropdown)
- Remove user info footer from sidebar (now in UserDropdown)
- Keep nav links and legal links in sidebar
- Simplify mobile bottom nav (4 items instead of 5, no sign-out — that's in the dropdown)

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/AppLayout.vue
git commit -m "refactor: AppLayout uses AppHeader, simplified sidebar"
```

---

## Task 7: Redesign Dashboard — Stats + AI Visibility Focus

**Files:**
- Modify: `frontend/src/pages/Dashboard.vue`

Full redesign focusing on: AI visibility status at the top, recent scans, clear Pro value, inline scan.

- [ ] **Step 1: Rewrite Dashboard.vue content (keep AppLayout wrapper)**

New layout structure:
1. **Hero area**: "Your AI Visibility" headline + overall status based on best scan score. For Pro: "AI agents are learning about your sites." For Free: "Your sites may be invisible to AI agents."
2. **Inline scan bar**: Domain input at top, always visible, prominent
3. **Stats row**: Total scans, avg score, best score, sites monitored (Pro)
4. **Recent scans**: Cards with score, domain, grade, site type badge, date. Clickable → report. Max 10.
5. **Pro features grid** (Free users): 2x2 grid showing locked features with "Unlock with Pro" overlay
6. **Pro dashboard** (Pro users): Monitored domains with scores, AI discovery status, quick compare

Replace the UpgradeCard CTA at the bottom with the new UpgradeCard component:
```html
<UpgradeCard v-if="!isPro" />
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/Dashboard.vue
git commit -m "feat: redesign dashboard with AI visibility focus and UpgradeCard"
```

---

## Task 8: Shift Pricing Page Messaging

**Files:**
- Modify: `frontend/src/pages/Pricing.vue`

Change the sales angle from "paid fixes when you need them" to "make AI agents recommend your site."

- [ ] **Step 1: Update Pricing.vue messaging**

Change headline from:
```
"Free scanning. Paid fixes when you need them."
```
To:
```
"Get found by AI agents"
```

Change subtitle from:
```
"Every website gets a full scan..."
```
To:
```
"Free scan tells you where you stand. Pro makes AI agents find and recommend your site."
```

Update Pro tier description to lead with outcomes:
- "AI agents start recommending your site"
- "Weekly monitoring ensures you stay visible"
- "AI Discovery Test verifies real results"

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/Pricing.vue
git commit -m "feat: shift pricing messaging to 'get found by AI agents'"
```

---

## Task 9: Update Landing Page Sales Messaging

**Files:**
- Modify: `frontend/src/pages/Landing.vue`

Shift the primary messaging from "how discoverable is your website" (passive/analytical) to "make your website discoverable" (active/transformative).

- [ ] **Step 1: Update hero headline and copy**

Change H1 from:
```
"How discoverable is your website for AI Agents?"
```
To:
```
"Make your website visible to AI Agents"
```

Change subheadline to be more action-oriented:
```
"ChatGPT, Claude, and Gemini are becoming how people find businesses.
Scan your site in 30 seconds, see what AI agents can't read, and get
the exact fixes to start getting recommended."
```

Update the "Don't just score — get found" section to be more specific about outcomes:
- Before: "Deploy fix files automatically"
- After: "We generate the exact files AI agents need to find your site — deploy them and start appearing in AI responses."

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/Landing.vue
git commit -m "feat: shift landing messaging to action-oriented 'make visible'"
```

---

## Task 10: Final Integration Test + Deploy

**Files:** None created — verification only.

- [ ] **Step 1: Build frontend locally**

Run: `cd frontend && npm run build`
Expected: Build succeeds with no errors.

- [ ] **Step 2: Test all page routes**

Open each in browser:
- `/` — Landing with AppHeader, clickable avatar if logged in
- `/pricing` — Updated messaging
- `/login` — AppHeader with back button
- `/dashboard` — Redesigned with AI visibility focus
- `/report/:id` — AppHeader with share action
- `/scan/:id` — AppHeader with back
- `/badge/:id` — AppHeader with back to report

- [ ] **Step 3: Test UserDropdown**

- Click avatar → dropdown opens
- Shows email, plan badge, menu items
- "Dashboard" navigates correctly
- "Manage billing" (Pro) opens Stripe portal
- "Sign out" clears session and redirects
- Click outside → dropdown closes

- [ ] **Step 4: Test mobile nav**

Resize to mobile width:
- Bottom nav shows on all AppLayout pages
- UserDropdown still works
- No horizontal overflow

- [ ] **Step 5: Commit and deploy**

```bash
git add -A
git commit -m "feat: complete UX overhaul — header, dashboard, messaging"
git push
ssh root@89.167.111.89 "cd /opt/agentready && git pull && docker compose build && docker compose up -d"
```

---

## Self-Review Checklist

- [x] **Spec coverage**: Header/profile (Tasks 1-2, 4-6), Dashboard redesign (Task 7), Sales messaging (Tasks 3, 8, 9), No breaking changes (incremental approach, existing functionality preserved)
- [x] **Placeholder scan**: All tasks have complete code blocks or specific instructions
- [x] **Type consistency**: UserDropdown imported consistently, AppHeader props match across pages, UpgradeCard props stable
- [x] **No orphaned imports**: Each task specifies what to import and what to remove
