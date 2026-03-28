# AgentReady

**Wie findbar ist dein Shop für AI Agents?**

Free Scanner Tool das Websites auf ihre Auffindbarkeit und Transaktionsfähigkeit für AI Shopping Agents prüft und einen Score + Fixes liefert.

## Features

- **Protocol Readiness** — UCP Endpoint, ai.txt, llms.txt, robots.txt AI-Policies
- **Structured Data Quality** — JSON-LD, Product/Offer Schema, Organization, Breadcrumbs
- **Agent Accessibility** — Response Time, JS Dependency, API Availability, URL Structure
- **Transaction Readiness** — Guest Checkout, Payment Methods, Shipping, Returns
- **Trust Signals** — Ratings, Security Headers, Contact Info

## Tech Stack

- **Backend:** FastAPI (Python)
- **Frontend:** Vue 3 + Tailwind CSS + Vite
- **Database:** SQLite
- **Deployment:** Docker + Nginx

## Quick Start

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Docker

```bash
docker-compose up --build
```

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/scan` | Start a new scan |
| GET | `/api/scan/{id}` | Get scan result |
| GET | `/api/health` | Health check |

## License

MIT
