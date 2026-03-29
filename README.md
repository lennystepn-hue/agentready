<div align="center">

# AgentCheck

### Is your website visible to AI agents?

**The open-source AI agent readiness scanner for any website.**

[Live Scanner](https://agentcheck.site) · [Report a Bug](https://github.com/lennystepn-hue/agentready/issues) · [Request Feature](https://github.com/lennystepn-hue/agentready/issues)

---

ChatGPT, Claude, Gemini, and Perplexity are becoming how people discover businesses, products, and content.
If your site isn't machine-readable, AI agents will recommend your competitors instead.

**AgentCheck scans any website and tells you exactly what to fix.**

</div>

---

## The Problem

AI agents are reshaping how people discover and interact with businesses online. By 2026, AI agents will drive **$20.9 billion** in retail spending alone ([Gartner, 2025](https://www.gartner.com)). But most websites aren't ready:

- No `llms.txt` or `ai.txt` — AI agents can't find basic site information
- Missing or incomplete Schema.org markup — agents can't read structured data
- No UCP endpoint — no programmatic capabilities for AI agents
- JavaScript-only rendering — agents see a blank page
- No structured conversion paths — agents can't guide users effectively

**The average website scores below 30/100 on AI agent readiness.**

AgentCheck runs **18+ automated checks** across 5 categories to surface exactly what's broken — and gives you copy-paste code to fix it.

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
4. Get your score + fix report  →  0-100 score, letter grade, prioritized fixes
```

### Example Output

```
Domain:     example-site.com
Type:       E-Commerce (auto-detected)
Score:      28 / 100
Grade:      E

Top Fixes:
  ✗ CRITICAL  UCP Endpoint missing              (+8 pts)
  ✗ CRITICAL  No Product Schema found            (+6 pts)
  ✗ CRITICAL  No JSON-LD structured data         (+5 pts)
  ⚠ WARNING   No ai.txt file                    (+4 pts)
  ⚠ WARNING   Content requires JavaScript        (+5 pts)
```

---

## Quick Start

### Try It Online

**[agentcheck.site](https://agentcheck.site)** — free, no registration required.

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
| `GET` | `/api/pricing` | Get pricing plans |

### Authenticated Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/auth/register` | Create account |
| `POST` | `/api/auth/login` | Sign in |
| `GET` | `/api/auth/me` | Get current user |
| `GET` | `/api/user/scans` | List user's scans |
| `GET` | `/api/scan/{id}/fixes` | Get tailored fix files (paid) |
| `GET` | `/api/scan/{id}/fixes/download` | Download fix ZIP (paid) |
| `POST` | `/api/compare` | Compare up to 4 domains (Pro) |
| `GET` | `/api/history/{domain}` | Score history (Pro) |
| `GET` | `/api/monitoring` | List monitored domains (Pro) |
| `POST` | `/api/monitoring` | Add domain to monitoring (Pro) |
| `POST` | `/api/checkout/session` | Create Stripe checkout |
| `POST` | `/api/billing/portal` | Stripe billing portal (Pro) |

### Scan Request Example

```bash
curl -X POST https://agentcheck.site/api/scan \
  -H "Content-Type: application/json" \
  -d '{"domain": "your-website.com"}'
```

Response:
```json
{
  "scan_id": "a1b2c3d4-...",
  "status": "pending",
  "message": "Scan started for your-website.com."
}
```

---

## Pricing

| | Free | Fix Files | Pro |
|---|---|---|---|
| **Price** | $0 | $9 one-time | $29/month |
| Scan + Score + Report | ✓ | ✓ | ✓ |
| Generic fix suggestions | ✓ | ✓ | ✓ |
| Shareable badge | ✓ | ✓ | ✓ |
| **Tailored fix files** (ai.txt, llms.txt, Schema, UCP) | — | 1 scan | Unlimited |
| **Implementation guide** | — | ✓ | ✓ |
| Weekly monitoring + alerts | — | — | ✓ |
| Competitor comparison | — | — | ✓ |
| Score history | — | — | ✓ |
| AI bot traffic tracking | — | — | ✓ |

---

## Fix Files — What You Get

When you purchase fix files for a scan, you receive a ZIP containing:

| File | Description |
|------|-------------|
| `ai.txt` | AI agent instructions, tailored to your site type |
| `llms.txt` | LLM context file describing your site and its content |
| `robots_txt_additions.txt` | Rules to add for GPTBot, ClaudeBot, PerplexityBot, etc. |
| `ucp.json` | Universal Commerce Protocol endpoint configuration |
| `schema_*.jsonld` | Schema template matching your site type (Product, Article, Restaurant, etc.) |
| `schema_organization.jsonld` | Organization Schema for your business |
| `implementation_guide.md` | Step-by-step deploy guide (Shopify, WooCommerce, custom) |

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

The script installs Docker, builds containers, obtains SSL certificates, and starts everything.

---

## Related Standards & Protocols

AgentCheck evaluates compatibility with these emerging AI standards:

- **[llms.txt](https://llmstxt.org)** — Markdown files that help LLMs understand your site
- **[ai.txt](https://ai-txt.org)** — AI agent instruction files (like robots.txt for AI)
- **[Schema.org](https://schema.org)** — Structured data vocabulary for products, articles, businesses, and more
- **[UCP (Universal Commerce Protocol)](https://www.ucprotocol.com)** — Programmatic commerce endpoint specification
- **robots.txt AI directives** — Crawl rules for GPTBot, ClaudeBot, PerplexityBot, Google-Extended

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

## FAQ

**Is this free?**
Yes. The scanner and reports are free forever. Tailored fix files and monitoring are paid.

**How accurate is the score?**
The score measures technical readiness signals that AI agents look for. It doesn't guarantee placement in AI responses, but sites with higher scores are significantly more likely to be found and recommended.

**Which AI agents does this cover?**
ChatGPT (OpenAI), Claude (Anthropic), Gemini (Google), Perplexity, and any agent that follows standard web protocols.

**Can I run this on my own server?**
Yes. AgentCheck is MIT licensed and fully self-hostable. See the Self-Hosting section above.

**What types of websites does this support?**
AgentCheck auto-detects your site type and adjusts checks accordingly. Supported types include e-commerce, blogs/news, SaaS, restaurants, local businesses, professional services, and portfolios/agencies.

**How is this different from regular SEO tools?**
Traditional SEO tools optimize for search engine crawlers. AgentCheck optimizes for AI agents — which read structured data, API endpoints, and machine-readable files that search crawlers ignore.

---

## Keywords

`ai agent readiness` `ai seo` `website ai readiness` `ai visibility for websites` `blog ai optimization` `saas ai optimization` `ecommerce ai optimization` `llms.txt` `ai.txt` `schema.org checker` `structured data validator` `ai agent visibility` `chatgpt` `claude` `ai product discovery` `machine readable website` `ucp protocol` `agent commerce protocol` `ai bot optimization` `is my site reachable for ai` `ai search optimization` `website ai scanner` `restaurant ai` `local business ai`

---

## License

[MIT](LICENSE) — Lenny Enderle, 2026

---

<div align="center">

**[Try AgentCheck Now](https://agentcheck.site)** — Free, no signup required.

Built by [Lenny Enderle](https://github.com/lennystepn-hue)

</div>
