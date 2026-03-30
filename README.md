<div align="center">

# AgentCheck

### AI is recommending your competitors. Not you.

**Free AI visibility scanner — check if ChatGPT, Claude, Perplexity, Gemini, Copilot & Google AI Overview can find your website.**

[Live Scanner](https://agentcheck.site) · [Report a Bug](https://github.com/lennystepn-hue/agentready/issues) · [Request Feature](https://github.com/lennystepn-hue/agentready/issues)

---

The next generation of customers won't Google you — they'll ask AI.
AgentCheck scans any website and shows you exactly which AI agents can find you, which can't, and what to fix.

**Your GEO & LLM SEO toolkit. Free, open source.**

</div>

---

## The Problem

AI agents are reshaping discovery. Millions of people skip Google and ask ChatGPT, Claude, or Perplexity for recommendations. If your website isn't machine-readable, you're invisible.

- No `llms.txt` or `ai.txt` — AI agents can't find basic site information
- Missing Schema.org markup — agents can't read structured data
- JavaScript-only rendering — agents see a blank page
- No AI-friendly protocols — you don't exist in the agentic web

**The average website scores below 30/100 on AI agent readiness.**

AgentCheck runs **18+ automated checks** across 5 categories, shows which LLMs can find you, and gives you copy-paste code to fix everything.

---

## Which AI Agents We Check

| AI Agent | What We Test |
|----------|-------------|
| **ChatGPT** (OpenAI) | llms.txt, ai.txt, structured data, protocol readiness |
| **Claude** (Anthropic) | Protocol readiness, agent accessibility, content structure |
| **Perplexity** | Structured data quality, trust signals, indexability |
| **Gemini** (Google) | Schema.org markup, crawl directives, structured data |
| **Copilot** (Microsoft) | AI protocols, structured data completeness |
| **Google AI Overview** | Schema markup, trust signals, crawl readiness |

Each scan produces a per-agent visibility grid: see exactly which AI can find you and which can't.

---

## What It Checks

| Category | Points | What It Measures |
|----------|--------|-----------------|
| **Protocol Readiness** | 20 | UCP endpoint, `ai.txt`, `llms.txt`, `robots.txt` AI bot rules |
| **Structured Data Quality** | 25 | JSON-LD, site-type Schema (Product, Article, Restaurant, etc.), Organization, Breadcrumbs |
| **Agent Accessibility** | 20 | TTFB, JavaScript dependency, API/feed availability, URL structure |
| **Conversion Readiness** | 20 | CTAs, contact forms, booking/checkout, site-type conversion signals |
| **Trust Signals** | 15 | Aggregate ratings, HTTPS + security headers, contact info |

Every check produces a **pass**, **warn**, or **fail** with a specific fix suggestion and code snippet.

---

## How It Works

```
1. Enter any website URL        →  agentcheck.site
2. We auto-detect site type     →  e-commerce, blog, SaaS, restaurant, etc.
3. We run 18+ automated checks  →  ~30 seconds
4. See which AI agents find you →  ChatGPT ✅, Claude ❌, Perplexity ✅ ...
5. Get your score + fix report  →  0-100 score, prioritized fixes with code
```

### Example Output

```
Domain:     example-store.com
Type:       E-Commerce (auto-detected)
Score:      28 / 100  —  Grade: E
Visibility: Mostly Hidden

  ChatGPT     ❌  Missing llms.txt
  Claude      ❌  Protocol readiness too low
  Perplexity  ⚠️  Weak structured data
  Gemini      ❌  Schema markup needed
  Copilot     ❌  Missing AI protocols
  AI Overview ❌  Trust signals too low

Top Fixes:
  ✗ CRITICAL  No Product Schema found            (+6 pts)
  ✗ CRITICAL  No JSON-LD structured data         (+5 pts)
  ⚠ WARNING   No ai.txt file                    (+4 pts)
  ⚠ WARNING   Content requires JavaScript        (+5 pts)
```

---

## Features

### Free
- AI readiness score (0-100) with letter grade
- Per-agent visibility grid (ChatGPT, Claude, Perplexity, Gemini, Copilot, AI Overview)
- Detailed report with 18+ checks across 5 categories
- Fix suggestions with code snippets
- Shareable report & badge

### Fix Files ($9 one-time)
- Ready-to-deploy `llms.txt`, `ai.txt`, Schema.org patches
- `robots.txt` AI agent rules
- Step-by-step implementation guide

### Pro ($29/month)
- **Hosted AI Files** — we serve your llms.txt & ai.txt for you
- **Agent Simulator** — watch how ChatGPT navigates your site step-by-step
- **AI Mention Tracking** — see how often LLMs cite your site
- **Crawler Ping** — notify AI crawlers when you update (3/day)
- **Competitor Comparison** — benchmark AI visibility vs rivals
- **Weekly Monitoring** — alerts when your score changes
- **Score History** — track improvements over time
- Unlimited fix file downloads

---

## Quick Start

### Try It Online

**[agentcheck.site](https://agentcheck.site)** — free, no signup required.

### Run Locally

```bash
# Clone
git clone https://github.com/lennystepn-hue/agentready.git
cd agentready

# Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` and scan your first domain.

### Docker (Production)

```bash
# Copy and configure environment
cp backend/.env.example backend/.env
# Edit .env with your keys

# Build and run
docker compose up --build -d
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.12, FastAPI, httpx, BeautifulSoup, aiosqlite |
| **Frontend** | Vue 3, Vite, Tailwind CSS, Composition API |
| **Database** | SQLite (persistent volume in Docker) |
| **Auth** | JWT (bcrypt + python-jose) |
| **Payments** | Stripe Checkout + Billing Portal |
| **Deployment** | Docker Compose, Nginx, Let's Encrypt SSL |
| **Monitoring** | APScheduler for weekly re-scans |

---

## API Reference

All endpoints are available at `https://agentcheck.site/api/`.

### Public Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/scan` | Start a new scan |
| `GET` | `/api/scan/{id}` | Get scan status/result |

### Authenticated Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/auth/register` | Create account |
| `POST` | `/api/auth/login` | Sign in |
| `GET` | `/api/auth/me` | Get current user |
| `GET` | `/api/user/scans` | List user's scans |
| `GET` | `/api/scan/{id}/fixes/download` | Download fix ZIP (paid) |
| `POST` | `/api/compare` | Compare up to 4 domains (Pro) |
| `GET` | `/api/history/{domain}` | Score history (Pro) |
| `GET` | `/api/monitoring` | List monitored domains (Pro) |
| `POST` | `/api/monitoring` | Add domain to monitoring (Pro) |
| `POST` | `/api/hosted-files/activate` | Activate hosted AI files (Pro) |
| `POST` | `/api/crawler-ping` | Ping AI crawlers (Pro, 3/day) |
| `POST` | `/api/simulate/{scanId}` | Run agent simulator (Pro) |
| `POST` | `/api/checkout/session` | Create Stripe checkout |
| `POST` | `/api/billing/portal` | Stripe billing portal |

### Scan Example

```bash
curl -X POST https://agentcheck.site/api/scan \
  -H "Content-Type: application/json" \
  -d '{"domain": "your-website.com"}'
```

```json
{
  "scan_id": "a1b2c3d4-...",
  "status": "pending",
  "message": "Scan started for your-website.com."
}
```

---

## Fix Files — What You Get

| File | Description |
|------|-------------|
| `llms.txt` | LLM context file describing your site — tailored to your site type |
| `ai.txt` | AI agent instructions with capabilities and endpoints |
| `robots_txt_additions.txt` | Rules for GPTBot, ClaudeBot, PerplexityBot, Google-Extended |
| `schema_*.jsonld` | Schema.org template matching your site type (Product, Article, Restaurant, etc.) |
| `schema_organization.jsonld` | Organization Schema for your business |
| `implementation_guide.md` | Step-by-step deploy guide (Shopify, WooCommerce, WordPress, custom) |

---

## Self-Hosting

AgentCheck is fully open source and designed to be self-hosted.

### Requirements

- VPS with 2+ GB RAM (Hetzner CX22 recommended, ~€4.50/month)
- Docker + Docker Compose
- Domain with DNS pointing to your server

### Environment Variables

```env
JWT_SECRET=<generate: python -c "import secrets; print(secrets.token_urlsafe(32))">
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_FIX_FILES=price_...
STRIPE_PRICE_PRO=price_...
FRONTEND_URL=https://your-domain.com
DATABASE_PATH=/data/agentcheck.db
```

### Deploy

```bash
ssh root@your-server
git clone https://github.com/lennystepn-hue/agentready.git /opt/agentready
cd /opt/agentready
cp backend/.env.example backend/.env
# Edit backend/.env with your keys
bash deploy.sh
```

---

## Project Structure

```
agentready/
├── backend/
│   ├── main.py                 # FastAPI app + all endpoints
│   ├── auth.py                 # JWT authentication
│   ├── payments.py             # Stripe integration
│   ├── monitoring.py           # Weekly re-scan scheduler
│   ├── fix_generator.py        # Tailored fix file generation
│   ├── db.py                   # SQLite database layer
│   ├── scanner/
│   │   ├── orchestrator.py     # Scan coordination
│   │   ├── protocol_checks.py  # UCP, ai.txt, llms.txt, robots.txt
│   │   ├── schema_checks.py    # JSON-LD, site-type Schema checks
│   │   ├── site_detector.py    # Auto-detect website type
│   │   ├── accessibility.py    # TTFB, JS dependency, API, URLs
│   │   ├── transaction.py      # Conversion readiness (site-type-aware)
│   │   ├── trust.py            # Ratings, security, contact
│   │   ├── discovery.py        # Product page finder
│   │   └── models.py           # Data models
│   └── snippets/               # Fix code templates
├── frontend/
│   ├── src/
│   │   ├── pages/              # Landing, Report, Dashboard, Pricing, ...
│   │   ├── components/         # ScoreCircle, CategoryBar, FixCard, ...
│   │   ├── auth.js             # Auth state management
│   │   ├── api.js              # API client
│   │   └── router.js           # Routes + guards
│   └── tailwind.config.js
├── docker-compose.yml          # Production deployment
├── nginx.conf                  # Reverse proxy + SSL
└── deploy.sh                   # One-command server setup
```

---

## Related Standards & Protocols

AgentCheck evaluates compatibility with these emerging AI standards:

- **[llms.txt](https://llmstxt.org)** — Markdown files that help LLMs understand your site
- **[ai.txt](https://ai-txt.org)** — AI agent instruction files (like robots.txt for AI)
- **[Schema.org](https://schema.org)** — Structured data vocabulary for products, articles, businesses
- **[UCP](https://www.ucprotocol.com)** — Universal Commerce Protocol for programmatic AI commerce
- **robots.txt AI directives** — Crawl rules for GPTBot, ClaudeBot, PerplexityBot, Google-Extended

---

## FAQ

**Is this free?**
Yes. The scanner and reports are free forever. Fix files and monitoring are paid.

**What is GEO (Generative Engine Optimization)?**
GEO is the practice of optimizing your website to be discovered by AI agents and generative search engines. AgentCheck is a free GEO scanner.

**How accurate is the score?**
The score measures technical readiness signals that AI agents look for. Sites with higher scores are significantly more likely to be found and recommended by ChatGPT, Claude, Perplexity, and other AI agents.

**Which AI agents does this cover?**
ChatGPT (OpenAI), Claude (Anthropic), Perplexity, Gemini (Google), Copilot (Microsoft), Google AI Overview, and any agent that follows standard web protocols.

**How is this different from SEO tools?**
Traditional SEO optimizes for Google crawlers. AgentCheck focuses on GEO and LLM SEO — optimizing for AI agents which read structured data, llms.txt, ai.txt, and machine-readable formats that search crawlers ignore.

**Can I self-host this?**
Yes. AgentCheck is MIT licensed and fully self-hostable. See the Self-Hosting section.

**What types of websites does this support?**
Auto-detects your site type: e-commerce, SaaS, blogs, restaurants, local businesses, professional services, portfolios, and more.

---

## Contributing

Contributions are welcome. Please open an issue first to discuss what you'd like to change.

```bash
# Fork + clone
git clone https://github.com/YOUR_USERNAME/agentready.git
cd agentready

# Install
cd backend && pip install -r requirements.txt
cd ../frontend && npm install

# Run
cd ../backend && uvicorn main:app --reload &
cd ../frontend && npm run dev
```

---

## Keywords

`AI agent readiness scanner` `GEO tool` `generative engine optimization` `LLM SEO` `AI visibility checker` `ChatGPT SEO` `AI search optimization` `llms.txt generator` `ai.txt checker` `Schema.org validator` `AI readiness score` `website AI scanner` `Perplexity SEO` `Claude AI discovery` `Copilot optimization` `Google AI Overview` `AEO` `AI engine optimization` `get found by AI` `AI commerce` `agentic web` `agent-ready website`

---

## License

[MIT](LICENSE) — Lenny Enderle, 2026

---

<div align="center">

**[Scan your website now](https://agentcheck.site)** — free, 30 seconds, no signup.

Built by [Lenny Enderle](https://github.com/lennystepn-hue)

</div>
