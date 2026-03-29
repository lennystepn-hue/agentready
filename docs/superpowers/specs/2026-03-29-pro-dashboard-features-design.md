# AgentCheck Pro Dashboard Features — Design Spec

## Goal

Transform the Pro dashboard from a passive scan viewer into an automated AI visibility engine that actively works in the background to get users' websites mentioned more often by AI agents.

## Core Principle

**"We don't just tell you what's wrong — we fix it, monitor it, and prove it's working."**

---

## Feature 1: Hosted Files Service

### What it does
Pro users click "Activate AI Files" and we generate + host `llms.txt`, `ai.txt`, and `robots_additions.txt` on our servers. The user sets up a simple redirect from their domain. We auto-update the files after every weekly re-scan.

### Technical Design

**Backend:**
- New table `hosted_files` (user_id, domain, file_type, content, public_token, is_active, created_at, updated_at)
- `public_token` = short unique ID (8 chars) for the hosted URL
- New endpoints:
  - `POST /api/hosted-files/activate` — generates files for user's most recent scan, stores in DB
  - `GET /api/hosted-files` — list user's hosted files with status
  - `GET /hosted/{token}/llms.txt` — public endpoint serving the hosted file (no auth, cached)
  - `GET /hosted/{token}/ai.txt` — same
  - `GET /hosted/{token}/robots.txt` — same
- Auto-update hook in monitoring cycle: after weekly re-scan, regenerate hosted files if score changed

**Frontend (Dashboard widget):**
- "Hosted AI Files" card showing:
  - Status per file (active/pending/not set up)
  - Hosted URLs for each file
  - "Copy redirect instructions" button with platform-specific guides (Nginx, Apache, Cloudflare, Shopify, WordPress)
  - Last updated timestamp
  - "Regenerate now" button

### Redirect Instructions (shown to user)
```
Add these redirects to your web server:

/llms.txt  →  https://agentcheck.site/hosted/abc123/llms.txt
/ai.txt    →  https://agentcheck.site/hosted/abc123/ai.txt

Shopify: Settings → Navigation → URL Redirects
WordPress: Redirection plugin or .htaccess
Nginx: rewrite ^/llms.txt$ https://agentcheck.site/hosted/abc123/llms.txt permanent;
```

---

## Feature 2: AI Crawler Ping Service

### What it does
After every file update or re-scan, we automatically notify AI crawlers and search engines that the site has new content. Users can also trigger manual pings.

### Technical Design

**Backend:**
- New module `backend/crawler_ping.py`
- Ping targets:
  1. IndexNow API (indexnow.org) — signals content updates to Bing/Yandex/search engines
  2. Google Sitemap Ping (`google.com/ping?sitemap=...`)
  3. Bing Sitemap Ping (`bing.com/ping?sitemap=...`)
  4. HEAD requests to user's key URLs (homepage, /llms.txt, /ai.txt, /sitemap.xml) — refreshes CDN caches
- New table `crawler_pings` (id, user_id, domain, ping_type, target_url, status_code, created_at)
- New endpoints:
  - `POST /api/crawler-ping` — manual ping (Pro, max 3/day)
  - `GET /api/crawler-ping/history` — ping history for dashboard
- Auto-trigger: after monitoring re-scan, after hosted file update

**Frontend (Dashboard widget):**
- "Crawler Status" card:
  - Last ping timestamp
  - Number of crawlers notified
  - "Ping now" button (with remaining pings today: "2/3 remaining")
  - Recent ping log (last 5)

---

## Feature 3: AI Mention Tracking

### What it does
Weekly automated queries to AI APIs checking if the user's domain appears in responses. Tracks trends over time.

### Technical Design

**Backend:**
- Extend existing `ai_discovery.py` to support scheduled batch runs
- New table `mention_tracking` (id, user_id, domain, week_date, queries_tested, queries_found, results_json, created_at)
- Run as part of weekly monitoring cycle: after re-scan, run discovery test, store results
- New endpoints:
  - `GET /api/mentions/{domain}` — mention history over time (Pro)
  - `GET /api/mentions/{domain}/latest` — latest week's results (Pro)

**Frontend (Dashboard widget):**
- "AI Visibility Trend" card:
  - Current week: "Found in 4/6 AI queries"
  - Trend arrow: ↑ +2 vs last week
  - Mini sparkline chart showing mentions over last 8 weeks
  - Breakdown: ChatGPT ✓, Claude ✓, Perplexity ✓, Gemini ✗
  - Click to expand full detail with query texts and context snippets

---

## Feature 4: Competitor Auto-Tracking

### What it does
Automatically identifies and weekly scans the top 3 competitors. Shows comparative scores on dashboard.

### Technical Design

**Backend:**
- Extend AI insights to auto-save competitor list per domain
- New table `competitor_tracking` (id, user_id, domain, competitor_domain, last_score, last_scan_id, created_at)
- Weekly monitoring cycle: after scanning user's domain, also scan top 3 competitors
- New endpoints:
  - `GET /api/competitors/{domain}` — competitor scores + history (Pro)
  - `POST /api/competitors/{domain}/add` — manually add competitor
  - `DELETE /api/competitors/{domain}/{competitor}` — remove competitor

**Frontend (Dashboard widget):**
- "Competitor Tracking" card:
  - Side-by-side: "You: 72 | rival-a.com: 45 | rival-b.com: 38"
  - Mini bar chart for visual comparison
  - Trend: "You're ahead of 2/3 competitors"
  - Link to full Compare page

---

## Feature 5: Content Optimizer

### What it does
GPT-4o-mini analyzes the user's page content and suggests AI-optimized rewrites for titles, meta descriptions, and key text.

### Technical Design

**Backend:**
- New module `backend/content_optimizer.py`
- Takes homepage HTML from latest scan, sends to GPT-4o-mini with prompt:
  "Rewrite these elements to be more easily parsed and recommended by AI agents"
- Targets: `<title>`, `<meta name="description">`, H1, first paragraph
- Results cached in new table `content_suggestions` (id, user_id, scan_id, suggestions_json, created_at)
- New endpoints:
  - `POST /api/content-optimize/{scan_id}` — generate suggestions (Pro)
  - `GET /api/content-optimize/{scan_id}` — get cached suggestions (Pro)

**Frontend (Dashboard widget):**
- "Content Suggestions" card:
  - Badge: "3 new suggestions"
  - List of suggestions with before/after preview
  - "Copy optimized text" button per suggestion
  - Generated once per scan, cached

---

## Feature 6: AI Agent Simulator

### What it does
Simulates a complete user journey as an AI agent would experience it. Tests: can an agent find products, read prices, reach checkout?

### Technical Design

**Backend:**
- New module `backend/agent_simulator.py`
- Steps (site-type-aware):
  - **E-commerce**: Find homepage → Find product listing → Read product details → Check price → Reach checkout
  - **Blog**: Find homepage → Find article listing → Read article → Find author info → Find RSS feed
  - **SaaS**: Find homepage → Find pricing → Find features → Find signup/demo → Find docs
  - **Restaurant**: Find homepage → Find menu → Find hours → Find reservation → Find location
- Each step: HTTP request + parse response, check if expected data is present
- Results: pass/fail per step, overall completion rate, specific blockers
- New table `agent_simulations` (id, user_id, scan_id, site_type, steps_json, completed_steps, total_steps, created_at)
- New endpoints:
  - `POST /api/simulate/{scan_id}` — run simulation (Pro)
  - `GET /api/simulate/{scan_id}` — get cached results (Pro)

**Frontend (Dashboard widget):**
- "Agent Simulation" card:
  - "Agent completed 3/5 steps"
  - Visual step flow with pass/fail icons
  - Specific blocker highlighted: "Blocked at: Checkout — no guest checkout detected"
  - "Re-run simulation" button

---

## Dashboard Layout

The new Pro dashboard has these sections top-to-bottom:

1. **Scan bar** (always visible)
2. **Hero row**: AI Visibility Score (big circle) + AI Mention Trend (sparkline)
3. **Automation row**: Hosted Files status + Crawler Ping status
4. **Intelligence row**: Competitor Tracking + Content Suggestions count
5. **Agent Simulation** (collapsible)
6. **Recent Scans** list

Free users see: Scan bar, basic score, recent scans, and UpgradeCard with "See what Pro automates for you" messaging.

---

## Cost Controls

- All GPT calls use `gpt-4o-mini` (~$0.15/1M tokens)
- AI Mention Tracking: max 6 queries/week/domain
- Content Optimizer: 1 generation per scan, cached
- Agent Simulator: 1 run per scan, cached
- Competitor scans: max 3 competitors per user
- Crawler pings: max 3 manual/day, 1 auto/week
- Everything cached in DB — no repeated API calls

---

## Database Changes Summary

New tables:
- `hosted_files` (user_id, domain, file_type, content, public_token, is_active, timestamps)
- `crawler_pings` (user_id, domain, ping_type, target_url, status_code, timestamp)
- `mention_tracking` (user_id, domain, week_date, queries_tested, queries_found, results_json)
- `competitor_tracking` (user_id, domain, competitor_domain, last_score, last_scan_id)
- `content_suggestions` (user_id, scan_id, suggestions_json)
- `agent_simulations` (user_id, scan_id, site_type, steps_json, completed_steps, total_steps)

---

## Implementation Priority

1. Hosted Files Service (highest value — "we do the work for you")
2. Crawler Ping Service (pairs with hosted files)
3. AI Mention Tracking (proves ROI — "see yourself getting found")
4. Competitor Auto-Tracking (competitive motivation)
5. Content Optimizer (quick GPT win)
6. Agent Simulator (impressive demo, complex to build)
