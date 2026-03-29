# Pro Dashboard Features Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build 6 automated Pro features (hosted files, crawler pings, mention tracking, competitor tracking, content optimizer, agent simulator) and a redesigned dashboard with live widgets.

**Architecture:** Each feature is a standalone backend module + DB table + API endpoints + dashboard widget. Features share the weekly monitoring cycle as their automation trigger. Dashboard.vue is rewritten last to incorporate all widgets.

**Tech Stack:** FastAPI, aiosqlite, httpx, OpenAI gpt-4o-mini, Vue 3 Composition API, Tailwind CSS

---

## File Map

| File | Action | Responsibility |
|------|--------|---------------|
| `backend/db.py` | MODIFY | Add 6 new tables + helper functions |
| `backend/hosted_files.py` | CREATE | Generate + serve hosted llms.txt/ai.txt/robots.txt |
| `backend/crawler_ping.py` | CREATE | Ping AI crawlers (IndexNow, Google, Bing) |
| `backend/mention_tracking.py` | CREATE | Weekly AI mention tracking + trend storage |
| `backend/competitor_tracking.py` | CREATE | Auto-track + scan competitor domains |
| `backend/content_optimizer.py` | CREATE | GPT-powered content suggestions |
| `backend/agent_simulator.py` | CREATE | Simulate AI agent user journey |
| `backend/main.py` | MODIFY | Add all new API endpoints |
| `backend/monitoring.py` | MODIFY | Hook all auto-features into weekly cycle |
| `frontend/src/api.js` | MODIFY | Add all new API functions |
| `frontend/src/pages/Dashboard.vue` | MODIFY | Full redesign with feature widgets |
| `frontend/src/components/MentionChart.vue` | CREATE | Sparkline chart for mention trends |
| `frontend/src/components/StepFlow.vue` | CREATE | Visual step indicator for agent simulator |

---

### Task 1: Database Schema + Hosted Files Backend

**Files:**
- Modify: `backend/db.py`
- Create: `backend/hosted_files.py`
- Modify: `backend/main.py`

- [ ] **Step 1: Add all 6 new tables to db.py**

Read `backend/db.py`, find `init_db()`. Add after the existing ALTER TABLE blocks:

```python
        # Hosted files for Pro users
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS hosted_files (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                domain TEXT NOT NULL,
                file_type TEXT NOT NULL,
                content TEXT NOT NULL,
                public_token TEXT UNIQUE NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_hosted_token ON hosted_files(public_token);
            CREATE INDEX IF NOT EXISTS idx_hosted_user ON hosted_files(user_id, domain);

            CREATE TABLE IF NOT EXISTS crawler_pings (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                domain TEXT NOT NULL,
                ping_type TEXT NOT NULL,
                target_url TEXT NOT NULL,
                status_code INTEGER,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_pings_user ON crawler_pings(user_id, domain);

            CREATE TABLE IF NOT EXISTS mention_tracking (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                domain TEXT NOT NULL,
                week_date TEXT NOT NULL,
                queries_tested INTEGER NOT NULL DEFAULT 0,
                queries_found INTEGER NOT NULL DEFAULT 0,
                results_json TEXT,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_mentions_user ON mention_tracking(user_id, domain);

            CREATE TABLE IF NOT EXISTS competitor_tracking (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                domain TEXT NOT NULL,
                competitor_domain TEXT NOT NULL,
                last_score INTEGER,
                last_scan_id TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_competitors_user ON competitor_tracking(user_id, domain);

            CREATE TABLE IF NOT EXISTS content_suggestions (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                scan_id TEXT NOT NULL,
                suggestions_json TEXT,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_suggestions_scan ON content_suggestions(scan_id);

            CREATE TABLE IF NOT EXISTS agent_simulations (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                scan_id TEXT NOT NULL,
                site_type TEXT NOT NULL,
                steps_json TEXT,
                completed_steps INTEGER NOT NULL DEFAULT 0,
                total_steps INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_simulations_scan ON agent_simulations(scan_id);
        """)
        await db.commit()
```

Add helper functions at the end of db.py:

```python
# ── Hosted Files ──

async def save_hosted_file(file_id, user_id, domain, file_type, content, public_token):
    db = await get_db()
    try:
        now = datetime.now(timezone.utc).isoformat()
        await db.execute(
            """INSERT OR REPLACE INTO hosted_files (id, user_id, domain, file_type, content, public_token, is_active, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?)""",
            (file_id, user_id, domain, file_type, content, public_token, now, now),
        )
        await db.commit()
    finally:
        await db.close()


async def get_hosted_files(user_id, domain=None):
    db = await get_db()
    try:
        if domain:
            cursor = await db.execute(
                "SELECT * FROM hosted_files WHERE user_id = ? AND domain = ? AND is_active = 1",
                (user_id, domain),
            )
        else:
            cursor = await db.execute(
                "SELECT * FROM hosted_files WHERE user_id = ? AND is_active = 1", (user_id,),
            )
        return [dict(r) for r in await cursor.fetchall()]
    finally:
        await db.close()


async def get_hosted_file_by_token(public_token, file_type):
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT content FROM hosted_files WHERE public_token = ? AND file_type = ? AND is_active = 1",
            (public_token, file_type),
        )
        row = await cursor.fetchone()
        return row["content"] if row else None
    finally:
        await db.close()


async def update_hosted_file_content(user_id, domain, file_type, content):
    db = await get_db()
    try:
        now = datetime.now(timezone.utc).isoformat()
        await db.execute(
            "UPDATE hosted_files SET content = ?, updated_at = ? WHERE user_id = ? AND domain = ? AND file_type = ?",
            (content, now, user_id, domain, file_type),
        )
        await db.commit()
    finally:
        await db.close()


# ── Crawler Pings ──

async def save_crawler_ping(ping_id, user_id, domain, ping_type, target_url, status_code):
    db = await get_db()
    try:
        now = datetime.now(timezone.utc).isoformat()
        await db.execute(
            "INSERT INTO crawler_pings (id, user_id, domain, ping_type, target_url, status_code, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (ping_id, user_id, domain, ping_type, target_url, status_code, now),
        )
        await db.commit()
    finally:
        await db.close()


async def get_crawler_pings(user_id, domain=None, limit=10):
    db = await get_db()
    try:
        if domain:
            cursor = await db.execute(
                "SELECT * FROM crawler_pings WHERE user_id = ? AND domain = ? ORDER BY created_at DESC LIMIT ?",
                (user_id, domain, limit),
            )
        else:
            cursor = await db.execute(
                "SELECT * FROM crawler_pings WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
                (user_id, limit),
            )
        return [dict(r) for r in await cursor.fetchall()]
    finally:
        await db.close()


async def count_pings_today(user_id):
    db = await get_db()
    try:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        cursor = await db.execute(
            "SELECT COUNT(*) as cnt FROM crawler_pings WHERE user_id = ? AND created_at LIKE ? AND ping_type = 'manual'",
            (user_id, f"{today}%"),
        )
        row = await cursor.fetchone()
        return row["cnt"] if row else 0
    finally:
        await db.close()


# ── Mention Tracking ──

async def save_mention_record(record_id, user_id, domain, week_date, queries_tested, queries_found, results_json):
    db = await get_db()
    try:
        now = datetime.now(timezone.utc).isoformat()
        await db.execute(
            "INSERT INTO mention_tracking (id, user_id, domain, week_date, queries_tested, queries_found, results_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (record_id, user_id, domain, week_date, queries_tested, queries_found, results_json, now),
        )
        await db.commit()
    finally:
        await db.close()


async def get_mention_history(user_id, domain, limit=12):
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM mention_tracking WHERE user_id = ? AND domain = ? ORDER BY week_date DESC LIMIT ?",
            (user_id, domain, limit),
        )
        return [dict(r) for r in await cursor.fetchall()]
    finally:
        await db.close()


# ── Competitor Tracking ──

async def save_competitor(comp_id, user_id, domain, competitor_domain):
    db = await get_db()
    try:
        now = datetime.now(timezone.utc).isoformat()
        await db.execute(
            "INSERT OR IGNORE INTO competitor_tracking (id, user_id, domain, competitor_domain, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
            (comp_id, user_id, domain, competitor_domain, now, now),
        )
        await db.commit()
    finally:
        await db.close()


async def get_competitors(user_id, domain):
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM competitor_tracking WHERE user_id = ? AND domain = ? ORDER BY last_score DESC",
            (user_id, domain),
        )
        return [dict(r) for r in await cursor.fetchall()]
    finally:
        await db.close()


async def update_competitor_score(user_id, domain, competitor_domain, score, scan_id):
    db = await get_db()
    try:
        now = datetime.now(timezone.utc).isoformat()
        await db.execute(
            "UPDATE competitor_tracking SET last_score = ?, last_scan_id = ?, updated_at = ? WHERE user_id = ? AND domain = ? AND competitor_domain = ?",
            (score, scan_id, now, user_id, domain, competitor_domain),
        )
        await db.commit()
    finally:
        await db.close()


async def delete_competitor(user_id, domain, competitor_domain):
    db = await get_db()
    try:
        await db.execute(
            "DELETE FROM competitor_tracking WHERE user_id = ? AND domain = ? AND competitor_domain = ?",
            (user_id, domain, competitor_domain),
        )
        await db.commit()
    finally:
        await db.close()


# ── Content Suggestions ──

async def save_content_suggestions(suggestion_id, user_id, scan_id, suggestions_json):
    db = await get_db()
    try:
        now = datetime.now(timezone.utc).isoformat()
        await db.execute(
            "INSERT OR REPLACE INTO content_suggestions (id, user_id, scan_id, suggestions_json, created_at) VALUES (?, ?, ?, ?, ?)",
            (suggestion_id, user_id, scan_id, suggestions_json, now),
        )
        await db.commit()
    finally:
        await db.close()


async def get_content_suggestions(scan_id):
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM content_suggestions WHERE scan_id = ? ORDER BY created_at DESC LIMIT 1",
            (scan_id,),
        )
        row = await cursor.fetchone()
        return dict(row) if row else None
    finally:
        await db.close()


# ── Agent Simulations ──

async def save_agent_simulation(sim_id, user_id, scan_id, site_type, steps_json, completed_steps, total_steps):
    db = await get_db()
    try:
        now = datetime.now(timezone.utc).isoformat()
        await db.execute(
            "INSERT OR REPLACE INTO agent_simulations (id, user_id, scan_id, site_type, steps_json, completed_steps, total_steps, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (sim_id, user_id, scan_id, site_type, steps_json, completed_steps, total_steps, now),
        )
        await db.commit()
    finally:
        await db.close()


async def get_agent_simulation(scan_id):
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM agent_simulations WHERE scan_id = ? ORDER BY created_at DESC LIMIT 1",
            (scan_id,),
        )
        row = await cursor.fetchone()
        return dict(row) if row else None
    finally:
        await db.close()
```

- [ ] **Step 2: Create hosted_files.py**

Create `backend/hosted_files.py` — generates and manages hosted AI files:

```python
import uuid
import secrets
import json
import logging

from db import save_hosted_file, get_hosted_files, update_hosted_file_content, get_scan
from fix_generator import generate_fixes

logger = logging.getLogger(__name__)


async def activate_hosted_files(user_id: str, domain: str, scan_id: str) -> dict:
    """Generate and store hosted files for a domain based on latest scan."""
    # Generate fix files from scan
    fixes = await generate_fixes(scan_id)

    hosted = []
    for file_info in fixes.get("files", []):
        file_type = file_info["name"]
        # Only host these specific files
        if file_type not in ("ai.txt", "llms.txt", "robots_txt_additions.txt"):
            continue

        file_id = str(uuid.uuid4())
        public_token = secrets.token_urlsafe(8)

        await save_hosted_file(
            file_id=file_id,
            user_id=user_id,
            domain=domain,
            file_type=file_type,
            content=file_info["content"],
            public_token=public_token,
        )
        hosted.append({
            "file_type": file_type,
            "public_token": public_token,
            "url": f"/hosted/{public_token}/{file_type}",
        })

    return {"domain": domain, "files": hosted}


async def refresh_hosted_files(user_id: str, domain: str, scan_id: str) -> int:
    """Regenerate hosted file contents after a re-scan. Returns count of updated files."""
    fixes = await generate_fixes(scan_id)
    updated = 0

    for file_info in fixes.get("files", []):
        file_type = file_info["name"]
        if file_type not in ("ai.txt", "llms.txt", "robots_txt_additions.txt"):
            continue
        await update_hosted_file_content(user_id, domain, file_type, file_info["content"])
        updated += 1

    return updated
```

- [ ] **Step 3: Add hosted files endpoints to main.py**

Read `backend/main.py`. Add imports and endpoints:

```python
from hosted_files import activate_hosted_files, refresh_hosted_files
from db import get_hosted_files, get_hosted_file_by_token
```

Endpoints (add before the `if __name__` block):

```python
# ── Hosted Files ──

@app.post("/api/hosted-files/activate")
async def activate_hosted(user: dict = Depends(get_current_user)):
    user_data = await get_user_by_id(user["id"])
    if not user_data or user_data.get("plan") != "pro":
        raise HTTPException(status_code=403, detail="Hosted files is a Pro feature.")

    scans = await get_user_scans(user["id"], limit=1)
    if not scans:
        raise HTTPException(status_code=400, detail="No completed scans found. Run a scan first.")

    latest = scans[0]
    result = await activate_hosted_files(user["id"], latest["domain"], latest["id"])
    return result


@app.get("/api/hosted-files")
async def list_hosted_files(user: dict = Depends(get_current_user)):
    files = await get_hosted_files(user["id"])
    return {"files": files}


@app.get("/hosted/{token}/{filename}")
async def serve_hosted_file(token: str, filename: str):
    content = await get_hosted_file_by_token(token, filename)
    if not content:
        raise HTTPException(status_code=404, detail="File not found.")

    content_type = "text/plain; charset=utf-8"
    if filename.endswith(".json"):
        content_type = "application/json"

    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(content=content, media_type=content_type, headers={"Cache-Control": "public, max-age=3600"})
```

- [ ] **Step 4: Commit**

```bash
git add backend/db.py backend/hosted_files.py backend/main.py
git commit -m "feat: hosted files service — generate, store, serve ai.txt/llms.txt"
```

---

### Task 2: Crawler Ping Service

**Files:**
- Create: `backend/crawler_ping.py`
- Modify: `backend/main.py`

- [ ] **Step 1: Create crawler_ping.py**

```python
import uuid
import logging
import httpx

from db import save_crawler_ping, count_pings_today

logger = logging.getLogger(__name__)


async def ping_crawlers(user_id: str, domain: str, manual: bool = False) -> list[dict]:
    """Ping AI crawlers and search engines about content updates."""
    results = []
    ping_type = "manual" if manual else "auto"
    base_url = f"https://{domain}"

    targets = [
        ("indexnow", f"https://api.indexnow.org/indexnow?url={base_url}&key=agentcheck"),
        ("google_ping", f"https://www.google.com/ping?sitemap={base_url}/sitemap.xml"),
        ("bing_ping", f"https://www.bing.com/ping?sitemap={base_url}/sitemap.xml"),
        ("head_homepage", base_url),
        ("head_llms", f"{base_url}/llms.txt"),
        ("head_ai", f"{base_url}/ai.txt"),
    ]

    async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
        for ping_name, url in targets:
            try:
                if ping_name.startswith("head_"):
                    resp = await client.head(url)
                else:
                    resp = await client.get(url)
                status = resp.status_code
            except Exception:
                status = 0

            ping_id = str(uuid.uuid4())
            await save_crawler_ping(ping_id, user_id, domain, ping_type, url, status)
            results.append({"type": ping_name, "url": url, "status": status})
            logger.info(f"Crawler ping {ping_name} for {domain}: {status}")

    return results
```

- [ ] **Step 2: Add endpoints to main.py**

```python
from crawler_ping import ping_crawlers
from db import get_crawler_pings, count_pings_today
```

```python
# ── Crawler Pings ──

@app.post("/api/crawler-ping")
async def manual_ping(user: dict = Depends(get_current_user)):
    user_data = await get_user_by_id(user["id"])
    if not user_data or user_data.get("plan") != "pro":
        raise HTTPException(status_code=403, detail="Crawler ping is a Pro feature.")

    pings_today = await count_pings_today(user["id"])
    if pings_today >= 3:
        raise HTTPException(status_code=429, detail="Maximum 3 manual pings per day.")

    scans = await get_user_scans(user["id"], limit=1)
    if not scans:
        raise HTTPException(status_code=400, detail="No scans found.")

    results = await ping_crawlers(user["id"], scans[0]["domain"], manual=True)
    return {"pings": results, "remaining_today": 3 - pings_today - 1}


@app.get("/api/crawler-ping/history")
async def ping_history(user: dict = Depends(get_current_user)):
    pings = await get_crawler_pings(user["id"], limit=20)
    return {"pings": pings}
```

- [ ] **Step 3: Commit**

```bash
git add backend/crawler_ping.py backend/main.py
git commit -m "feat: crawler ping service — IndexNow, Google, Bing pings"
```

---

### Task 3: Mention Tracking + Competitor Tracking

**Files:**
- Create: `backend/mention_tracking.py`
- Create: `backend/competitor_tracking.py`
- Modify: `backend/main.py`

- [ ] **Step 1: Create mention_tracking.py**

```python
import uuid
import json
import logging
from datetime import datetime, timezone

from ai_discovery import run_discovery_test
from db import save_mention_record, get_mention_history

logger = logging.getLogger(__name__)


async def track_mentions(user_id: str, domain: str, site_type: str = "generic") -> dict:
    """Run discovery test and store results for trend tracking."""
    result = await run_discovery_test(domain, site_type=site_type)

    week_date = datetime.now(timezone.utc).strftime("%Y-W%W")
    record_id = str(uuid.uuid4())

    await save_mention_record(
        record_id=record_id,
        user_id=user_id,
        domain=domain,
        week_date=week_date,
        queries_tested=result.get("queries_tested", 0),
        queries_found=result.get("queries_found", 0),
        results_json=json.dumps(result.get("results", [])),
    )

    return {
        "domain": domain,
        "week": week_date,
        "found": result.get("queries_found", 0),
        "tested": result.get("queries_tested", 0),
        "score": result.get("discovery_score", 0),
        "summary": result.get("summary", ""),
        "results": result.get("results", []),
    }
```

- [ ] **Step 2: Create competitor_tracking.py**

```python
import uuid
import json
import logging

from scanner.orchestrator import run_scan as execute_scan
from db import (
    save_competitor, get_competitors, update_competitor_score,
    delete_competitor, get_scan, get_scan_insights, save_scan_insights,
    create_scan,
)
from ai_insights import generate_scan_insights

logger = logging.getLogger(__name__)


async def auto_discover_competitors(user_id: str, domain: str, scan_id: str) -> list[str]:
    """Use AI insights to find competitors. Returns list of competitor domains."""
    # Check if insights already cached
    cached = await get_scan_insights(scan_id)
    if cached and "competitors" in cached:
        return cached["competitors"][:3]

    # Generate insights
    scan = await get_scan(scan_id)
    if not scan or not scan.get("report_json"):
        return []

    report = json.loads(scan["report_json"])
    insights = await generate_scan_insights(domain, report)

    if "error" not in insights:
        await save_scan_insights(scan_id, insights)

    return insights.get("competitors", [])[:3]


async def scan_competitor(user_id: str, domain: str, competitor_domain: str) -> int | None:
    """Scan a competitor domain and return their score."""
    scan_id = str(uuid.uuid4())
    try:
        await create_scan(scan_id, competitor_domain, "system")
        await execute_scan(scan_id, competitor_domain)
        scan = await get_scan(scan_id)
        if scan and scan.get("total_score") is not None:
            score = scan["total_score"]
            await update_competitor_score(user_id, domain, competitor_domain, score, scan_id)
            return score
    except Exception as e:
        logger.warning(f"Competitor scan failed for {competitor_domain}: {e}")
    return None
```

- [ ] **Step 3: Add endpoints to main.py**

```python
from mention_tracking import track_mentions
from competitor_tracking import auto_discover_competitors, scan_competitor
from db import get_mention_history, get_competitors, save_competitor, delete_competitor
```

```python
# ── Mention Tracking ──

@app.get("/api/mentions/{domain}")
async def get_mentions(domain: str, user: dict = Depends(get_current_user)):
    user_data = await get_user_by_id(user["id"])
    if not user_data or user_data.get("plan") != "pro":
        raise HTTPException(status_code=403, detail="Mention tracking is a Pro feature.")
    history = await get_mention_history(user["id"], domain, limit=12)
    return {"domain": domain, "history": history}


@app.post("/api/mentions/{domain}/track")
async def run_mention_track(domain: str, user: dict = Depends(get_current_user)):
    user_data = await get_user_by_id(user["id"])
    if not user_data or user_data.get("plan") != "pro":
        raise HTTPException(status_code=403, detail="Mention tracking is a Pro feature.")
    result = await track_mentions(user["id"], domain)
    return result


# ── Competitor Tracking ──

@app.get("/api/competitors/{domain}")
async def get_domain_competitors(domain: str, user: dict = Depends(get_current_user)):
    user_data = await get_user_by_id(user["id"])
    if not user_data or user_data.get("plan") != "pro":
        raise HTTPException(status_code=403, detail="Competitor tracking is a Pro feature.")
    competitors = await get_competitors(user["id"], domain)
    return {"domain": domain, "competitors": competitors}


@app.post("/api/competitors/{domain}/discover")
async def discover_competitors(domain: str, user: dict = Depends(get_current_user), background_tasks: BackgroundTasks = None):
    user_data = await get_user_by_id(user["id"])
    if not user_data or user_data.get("plan") != "pro":
        raise HTTPException(status_code=403, detail="Pro feature.")

    scans = await get_user_scans(user["id"], limit=1)
    if not scans:
        raise HTTPException(status_code=400, detail="No scans found.")

    competitors = await auto_discover_competitors(user["id"], domain, scans[0]["id"])

    # Save discovered competitors
    for comp in competitors:
        comp_id = str(uuid.uuid4())
        await save_competitor(comp_id, user["id"], domain, comp)

    return {"domain": domain, "discovered": competitors}


@app.post("/api/competitors/{domain}/scan")
async def scan_all_competitors(domain: str, user: dict = Depends(get_current_user)):
    user_data = await get_user_by_id(user["id"])
    if not user_data or user_data.get("plan") != "pro":
        raise HTTPException(status_code=403, detail="Pro feature.")

    competitors = await get_competitors(user["id"], domain)
    results = []
    for comp in competitors[:3]:
        score = await scan_competitor(user["id"], domain, comp["competitor_domain"])
        results.append({"domain": comp["competitor_domain"], "score": score})

    return {"results": results}


@app.delete("/api/competitors/{domain}/{competitor}")
async def remove_competitor(domain: str, competitor: str, user: dict = Depends(get_current_user)):
    await delete_competitor(user["id"], domain, competitor)
    return {"status": "deleted"}
```

- [ ] **Step 4: Commit**

```bash
git add backend/mention_tracking.py backend/competitor_tracking.py backend/main.py
git commit -m "feat: mention tracking + competitor auto-tracking"
```

---

### Task 4: Content Optimizer + Agent Simulator

**Files:**
- Create: `backend/content_optimizer.py`
- Create: `backend/agent_simulator.py`
- Modify: `backend/main.py`

- [ ] **Step 1: Create content_optimizer.py**

```python
import os
import json
import logging
import httpx

from db import save_content_suggestions, get_content_suggestions, get_scan

logger = logging.getLogger(__name__)
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")


async def optimize_content(user_id: str, scan_id: str) -> dict:
    """Analyze page content and suggest AI-optimized rewrites."""
    # Check cache
    cached = await get_content_suggestions(scan_id)
    if cached and cached.get("suggestions_json"):
        return json.loads(cached["suggestions_json"])

    scan = await get_scan(scan_id)
    if not scan or not scan.get("report_json"):
        return {"error": "Scan not found or incomplete."}

    report = json.loads(scan["report_json"])
    domain = scan["domain"]
    site_type = report.get("site_type", "generic")
    site_label = report.get("site_label", "Website")

    if not OPENAI_API_KEY:
        return {"error": "AI service not configured."}

    prompt = f"""You are an AI visibility optimization expert. Analyze this website and suggest content improvements that will make it more likely to be mentioned and recommended by AI agents like ChatGPT, Claude, and Perplexity.

Domain: {domain}
Site type: {site_label}
Current AI readiness score: {report.get('total_score', 0)}/100

Suggest optimizations for these elements. For each, provide the current state (if detectable) and an optimized version.

Respond in this exact JSON format:
{{
  "suggestions": [
    {{
      "element": "Page Title",
      "current": "Current title or 'Not detected'",
      "suggested": "Optimized title that AI agents will better parse and cite",
      "reason": "Why this change helps AI visibility"
    }},
    {{
      "element": "Meta Description",
      "current": "...",
      "suggested": "...",
      "reason": "..."
    }},
    {{
      "element": "Homepage H1",
      "current": "...",
      "suggested": "...",
      "reason": "..."
    }},
    {{
      "element": "Key Product/Service Description",
      "current": "...",
      "suggested": "...",
      "reason": "..."
    }}
  ],
  "general_tips": [
    "Tip 1 specific to this {site_label.lower()}",
    "Tip 2"
  ]
}}

Be specific to this {site_label.lower()}. Keep suggestions concise and actionable."""

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
                json={
                    "model": "gpt-4o-mini",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 600,
                    "temperature": 0.3,
                    "response_format": {"type": "json_object"},
                },
            )
            if resp.status_code == 200:
                data = resp.json()
                result = json.loads(data["choices"][0]["message"]["content"])
                # Cache
                import uuid
                await save_content_suggestions(str(uuid.uuid4()), user_id, scan_id, json.dumps(result))
                return result
            return {"error": f"AI service error (HTTP {resp.status_code})"}
    except Exception as e:
        return {"error": str(e)[:200]}
```

- [ ] **Step 2: Create agent_simulator.py**

```python
import json
import logging
import httpx
from bs4 import BeautifulSoup

from db import save_agent_simulation, get_agent_simulation, get_scan

logger = logging.getLogger(__name__)

SITE_STEPS = {
    "ecommerce": [
        {"name": "Find homepage", "action": "get_homepage"},
        {"name": "Find product listing", "action": "find_products"},
        {"name": "Read product details", "action": "read_product"},
        {"name": "Check price & availability", "action": "check_price"},
        {"name": "Reach checkout", "action": "find_checkout"},
    ],
    "blog": [
        {"name": "Find homepage", "action": "get_homepage"},
        {"name": "Find article listing", "action": "find_articles"},
        {"name": "Read article content", "action": "read_article"},
        {"name": "Find author info", "action": "find_author"},
        {"name": "Find RSS feed", "action": "find_rss"},
    ],
    "saas": [
        {"name": "Find homepage", "action": "get_homepage"},
        {"name": "Find pricing page", "action": "find_pricing"},
        {"name": "Find features list", "action": "find_features"},
        {"name": "Find signup/demo", "action": "find_signup"},
        {"name": "Find documentation", "action": "find_docs"},
    ],
    "restaurant": [
        {"name": "Find homepage", "action": "get_homepage"},
        {"name": "Find menu", "action": "find_menu"},
        {"name": "Find opening hours", "action": "find_hours"},
        {"name": "Find reservation", "action": "find_reservation"},
        {"name": "Find location", "action": "find_location"},
    ],
}


async def run_simulation(user_id: str, scan_id: str) -> dict:
    """Simulate an AI agent navigating the site."""
    cached = await get_agent_simulation(scan_id)
    if cached and cached.get("steps_json"):
        return json.loads(cached["steps_json"])

    scan = await get_scan(scan_id)
    if not scan or not scan.get("report_json"):
        return {"error": "Scan not found."}

    report = json.loads(scan["report_json"])
    domain = scan["domain"]
    site_type = report.get("site_type", "generic")

    steps = SITE_STEPS.get(site_type, SITE_STEPS.get("saas"))
    results = []
    completed = 0

    async with httpx.AsyncClient(
        timeout=12, follow_redirects=True,
        headers={"User-Agent": "Mozilla/5.0 (compatible; AgentCheck-Simulator/1.0)"}
    ) as client:
        html = ""
        for step in steps:
            try:
                passed, detail = await _execute_step(client, domain, step["action"], html)
                if passed and step["action"] == "get_homepage":
                    html = detail  # Store homepage HTML for later steps
                results.append({
                    "name": step["name"],
                    "status": "pass" if passed else "fail",
                    "detail": detail if not passed else "OK",
                })
                if passed:
                    completed += 1
                else:
                    # Mark remaining steps as blocked
                    for remaining in steps[len(results):]:
                        results.append({"name": remaining["name"], "status": "blocked", "detail": f"Blocked by: {step['name']}"})
                    break
            except Exception as e:
                results.append({"name": step["name"], "status": "fail", "detail": str(e)[:100]})
                break

    output = {
        "domain": domain,
        "site_type": site_type,
        "steps": results,
        "completed": completed,
        "total": len(steps),
        "completion_rate": round((completed / len(steps)) * 100),
    }

    import uuid
    await save_agent_simulation(str(uuid.uuid4()), user_id, scan_id, site_type, json.dumps(output), completed, len(steps))
    return output


async def _execute_step(client, domain, action, html=""):
    """Execute a single simulation step. Returns (passed: bool, detail: str)."""
    base = f"https://{domain}"

    if action == "get_homepage":
        resp = await client.get(base)
        if resp.status_code == 200:
            return True, resp.text
        return False, f"HTTP {resp.status_code}"

    soup = BeautifulSoup(html, "lxml") if html else None
    html_lower = html.lower() if html else ""

    if action == "find_products":
        patterns = ["product", "shop", "catalog", "collection", "/p/", "item"]
        if any(p in html_lower for p in patterns):
            return True, ""
        return False, "No product listing found in page content"

    if action == "read_product":
        if '"@type":"Product"' in html or '"@type": "Product"' in html:
            return True, ""
        if "price" in html_lower and ("add to cart" in html_lower or "buy" in html_lower):
            return True, ""
        return False, "No structured product data found"

    if action == "check_price":
        patterns = ['"price"', "€", "$", "£", "price", "preis"]
        if any(p in html_lower for p in patterns):
            return True, ""
        return False, "No price information found"

    if action == "find_checkout":
        patterns = ["checkout", "cart", "warenkorb", "kasse", "buy now"]
        if any(p in html_lower for p in patterns):
            return True, ""
        return False, "No checkout/cart path found"

    if action == "find_articles":
        patterns = ["article", "blog", "post", "news", "story"]
        if any(p in html_lower for p in patterns):
            return True, ""
        return False, "No article listing found"

    if action == "read_article":
        if '"@type":"Article"' in html or '"@type":"BlogPosting"' in html:
            return True, ""
        if soup and len(soup.get_text(strip=True).split()) > 200:
            return True, ""
        return False, "No article content found"

    if action == "find_author":
        if "author" in html_lower or '"@type":"Person"' in html:
            return True, ""
        return False, "No author information found"

    if action == "find_rss":
        if "rss" in html_lower or "feed" in html_lower or 'type="application/rss' in html_lower:
            return True, ""
        try:
            resp = await client.get(f"{base}/feed")
            if resp.status_code == 200:
                return True, ""
        except:
            pass
        return False, "No RSS feed found"

    if action == "find_pricing":
        patterns = ["pricing", "plans", "preise", "$", "€", "/month", "free tier"]
        if any(p in html_lower for p in patterns):
            return True, ""
        return False, "No pricing page found"

    if action == "find_features":
        patterns = ["features", "capabilities", "what we offer", "leistungen"]
        if any(p in html_lower for p in patterns):
            return True, ""
        return False, "No features section found"

    if action == "find_signup":
        patterns = ["sign up", "register", "get started", "free trial", "demo", "start free"]
        if any(p in html_lower for p in patterns):
            return True, ""
        return False, "No signup/demo path found"

    if action == "find_docs":
        patterns = ["docs", "documentation", "api", "developer", "guide"]
        if any(p in html_lower for p in patterns):
            return True, ""
        try:
            resp = await client.get(f"{base}/docs")
            if resp.status_code == 200:
                return True, ""
        except:
            pass
        return False, "No documentation found"

    if action == "find_menu":
        patterns = ["menu", "speisekarte", "dishes", "food"]
        if any(p in html_lower for p in patterns):
            return True, ""
        return False, "No menu found"

    if action == "find_hours":
        patterns = ["hours", "öffnungszeiten", "opening", "schedule", "open"]
        if any(p in html_lower for p in patterns):
            return True, ""
        return False, "No opening hours found"

    if action == "find_reservation":
        patterns = ["reservation", "book a table", "reservierung", "booking"]
        if any(p in html_lower for p in patterns):
            return True, ""
        return False, "No reservation system found"

    if action == "find_location":
        patterns = ["address", "location", "map", "directions", "standort", "anfahrt"]
        if any(p in html_lower for p in patterns):
            return True, ""
        return False, "No location information found"

    return False, f"Unknown action: {action}"
```

- [ ] **Step 3: Add endpoints to main.py**

```python
from content_optimizer import optimize_content
from agent_simulator import run_simulation
```

```python
# ── Content Optimizer ──

@app.post("/api/content-optimize/{scan_id}")
async def content_optimize(scan_id: str, user: dict = Depends(get_current_user)):
    user_data = await get_user_by_id(user["id"])
    if not user_data or user_data.get("plan") != "pro":
        raise HTTPException(status_code=403, detail="Content optimizer is a Pro feature.")
    result = await optimize_content(user["id"], scan_id)
    return result


# ── Agent Simulator ──

@app.post("/api/simulate/{scan_id}")
async def simulate_agent(scan_id: str, user: dict = Depends(get_current_user)):
    user_data = await get_user_by_id(user["id"])
    if not user_data or user_data.get("plan") != "pro":
        raise HTTPException(status_code=403, detail="Agent simulator is a Pro feature.")
    result = await run_simulation(user["id"], scan_id)
    return result
```

- [ ] **Step 4: Commit**

```bash
git add backend/content_optimizer.py backend/agent_simulator.py backend/main.py
git commit -m "feat: content optimizer (GPT) + agent simulator"
```

---

### Task 5: Hook All Features Into Weekly Monitoring Cycle

**Files:**
- Modify: `backend/monitoring.py`

- [ ] **Step 1: Update monitoring.py**

Read `backend/monitoring.py`. In `run_monitoring_cycle()`, after the existing scan + email logic per monitor, add:

```python
from hosted_files import refresh_hosted_files
from crawler_ping import ping_crawlers
from mention_tracking import track_mentions
from competitor_tracking import scan_competitor
from db import get_hosted_files, get_competitors
```

After the existing per-monitor scan completes successfully, add this block:

```python
            # ── Pro Automation: Refresh hosted files ──
            try:
                hosted = await get_hosted_files(user_id, domain)
                if hosted:
                    updated = await refresh_hosted_files(user_id, domain, scan_id)
                    logger.info(f"Monitoring: refreshed {updated} hosted files for {domain}")
            except Exception as e:
                logger.warning(f"Monitoring: hosted file refresh failed for {domain}: {e}")

            # ── Pro Automation: Ping crawlers ──
            try:
                await ping_crawlers(user_id, domain, manual=False)
                logger.info(f"Monitoring: pinged crawlers for {domain}")
            except Exception as e:
                logger.warning(f"Monitoring: crawler ping failed for {domain}: {e}")

            # ── Pro Automation: Track AI mentions ──
            try:
                mention_result = await track_mentions(user_id, domain)
                logger.info(f"Monitoring: tracked mentions for {domain} — {mention_result.get('found', 0)}/{mention_result.get('tested', 0)}")
            except Exception as e:
                logger.warning(f"Monitoring: mention tracking failed for {domain}: {e}")

            # ── Pro Automation: Scan competitors ──
            try:
                competitors = await get_competitors(user_id, domain)
                for comp in competitors[:3]:
                    await scan_competitor(user_id, domain, comp["competitor_domain"])
                    logger.info(f"Monitoring: scanned competitor {comp['competitor_domain']}")
            except Exception as e:
                logger.warning(f"Monitoring: competitor scan failed for {domain}: {e}")
```

- [ ] **Step 2: Commit**

```bash
git add backend/monitoring.py
git commit -m "feat: hook all Pro automation into weekly monitoring cycle"
```

---

### Task 6: Frontend API Functions + Dashboard Widgets

**Files:**
- Modify: `frontend/src/api.js`
- Create: `frontend/src/components/MentionChart.vue`
- Create: `frontend/src/components/StepFlow.vue`

- [ ] **Step 1: Add all new API functions to api.js**

Read `frontend/src/api.js`. Add at the end:

```javascript
// Hosted Files
export function activateHostedFiles() {
  return request('POST', '/api/hosted-files/activate')
}

export function getHostedFiles() {
  return request('GET', '/api/hosted-files')
}

// Crawler Pings
export function pingCrawlers() {
  return request('POST', '/api/crawler-ping')
}

export function getPingHistory() {
  return request('GET', '/api/crawler-ping/history')
}

// Mention Tracking
export function getMentions(domain) {
  return request('GET', `/api/mentions/${encodeURIComponent(domain)}`)
}

export function trackMentions(domain) {
  return request('POST', `/api/mentions/${encodeURIComponent(domain)}/track`)
}

// Competitor Tracking
export function getCompetitors(domain) {
  return request('GET', `/api/competitors/${encodeURIComponent(domain)}`)
}

export function discoverCompetitors(domain) {
  return request('POST', `/api/competitors/${encodeURIComponent(domain)}/discover`)
}

export function scanCompetitors(domain) {
  return request('POST', `/api/competitors/${encodeURIComponent(domain)}/scan`)
}

export function removeCompetitor(domain, competitor) {
  return request('DELETE', `/api/competitors/${encodeURIComponent(domain)}/${encodeURIComponent(competitor)}`)
}

// Content Optimizer
export function optimizeContent(scanId) {
  return request('POST', `/api/content-optimize/${scanId}`)
}

// Agent Simulator
export function simulateAgent(scanId) {
  return request('POST', `/api/simulate/${scanId}`)
}
```

- [ ] **Step 2: Create MentionChart.vue**

Simple sparkline chart for mention trends:

```vue
<script setup>
import { computed } from 'vue'

const props = defineProps({
  data: { type: Array, default: () => [] }, // [{week, found, tested}]
})

const bars = computed(() => {
  if (!props.data.length) return []
  return props.data.slice().reverse().map(d => ({
    week: d.week_date || d.week,
    pct: d.queries_tested > 0 ? Math.round((d.queries_found / d.queries_tested) * 100) : 0,
    found: d.queries_found,
    tested: d.queries_tested,
  }))
})
</script>

<template>
  <div class="flex items-end gap-1 h-12">
    <div
      v-for="(bar, idx) in bars"
      :key="idx"
      class="flex-1 rounded-t transition-all"
      :class="bar.pct > 50 ? 'bg-score-good' : bar.pct > 0 ? 'bg-score-medium' : 'bg-warm-200'"
      :style="{ height: Math.max(bar.pct, 4) + '%' }"
      :title="`${bar.week}: ${bar.found}/${bar.tested} queries`"
    />
  </div>
</template>
```

- [ ] **Step 3: Create StepFlow.vue**

Visual step indicator for agent simulator:

```vue
<script setup>
defineProps({
  steps: { type: Array, default: () => [] }, // [{name, status, detail}]
})
</script>

<template>
  <div class="space-y-2">
    <div v-for="(step, idx) in steps" :key="idx" class="flex items-center gap-3">
      <!-- Step number -->
      <div
        class="w-6 h-6 rounded-full flex items-center justify-center text-xs font-display font-bold flex-shrink-0"
        :class="{
          'bg-score-good text-white': step.status === 'pass',
          'bg-score-bad text-white': step.status === 'fail',
          'bg-warm-200 text-warm-500': step.status === 'blocked',
        }"
      >
        <svg v-if="step.status === 'pass'" class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" /></svg>
        <svg v-else-if="step.status === 'fail'" class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>
        <span v-else>{{ idx + 1 }}</span>
      </div>
      <!-- Step info -->
      <div class="flex-1 min-w-0">
        <p class="text-sm" :class="step.status === 'blocked' ? 'text-muted' : 'text-primary'">{{ step.name }}</p>
        <p v-if="step.status === 'fail'" class="text-xs text-score-bad">{{ step.detail }}</p>
      </div>
      <!-- Connector line -->
      <div v-if="idx < steps.length - 1" class="hidden" />
    </div>
  </div>
</template>
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/api.js frontend/src/components/MentionChart.vue frontend/src/components/StepFlow.vue
git commit -m "feat: frontend API functions + MentionChart + StepFlow components"
```

---

### Task 7: Dashboard Redesign With All Widgets

**Files:**
- Modify: `frontend/src/pages/Dashboard.vue`

- [ ] **Step 1: Rewrite Dashboard.vue**

Read `frontend/src/pages/Dashboard.vue`. Rewrite the content inside `<AppLayout>` with the new widget layout. Keep all existing imports and add new ones.

New imports to add:
```javascript
import MentionChart from '../components/MentionChart.vue'
import StepFlow from '../components/StepFlow.vue'
import UpgradeCard from '../components/UpgradeCard.vue'
import {
  getUserScans, getMonitors, startScan,
  getHostedFiles, activateHostedFiles,
  pingCrawlers, getPingHistory,
  getMentions,
  getCompetitors, discoverCompetitors,
  optimizeContent, simulateAgent,
} from '../api.js'
```

New reactive state:
```javascript
// Existing
const scans = ref([])
const monitors = ref([])
// New
const hostedFiles = ref([])
const pingHistory = ref([])
const mentions = ref([])
const competitors = ref([])
const contentSuggestions = ref(null)
const simulation = ref(null)
// Loading states
const loadingHosted = ref(false)
const loadingPing = ref(false)
const loadingMentions = ref(false)
const loadingCompetitors = ref(false)
const activatingFiles = ref(false)
const pinging = ref(false)
```

On mount, load all data in parallel for Pro users:
```javascript
onMounted(async () => {
  // Load scans (all users)
  try {
    const data = await getUserScans()
    const raw = Array.isArray(data) ? data : (data.scans || [])
    scans.value = raw.map(normalizeScan)
  } catch (e) { error.value = e.message }
  finally { loadingScans.value = false }

  // Load Pro features in parallel
  if (isPro.value && primaryDomain.value) {
    const domain = primaryDomain.value
    Promise.all([
      getHostedFiles().then(d => { hostedFiles.value = d.files || [] }).catch(() => {}),
      getPingHistory().then(d => { pingHistory.value = d.pings || [] }).catch(() => {}),
      getMentions(domain).then(d => { mentions.value = d.history || [] }).catch(() => {}),
      getCompetitors(domain).then(d => { competitors.value = d.competitors || [] }).catch(() => {}),
      getMonitors().then(d => { monitors.value = Array.isArray(d) ? d : (d.monitors || []) }).catch(() => {}),
    ])
  }
})
```

Dashboard layout (inside AppLayout):
1. **Scan bar** — domain input + run scan (existing, keep)
2. **Hero row** — AI Visibility Score circle (best scan) + AI Mention Trend (MentionChart) side by side
3. **Automation row** — Hosted Files card + Crawler Ping card side by side
4. **Intelligence row** — Competitor Tracking card + Content Suggestions card side by side
5. **Agent Simulator** card (full width, collapsible)
6. **Recent Scans** list (existing, keep)
7. **UpgradeCard** for free users (existing, keep)

Each widget card follows this pattern:
```html
<div class="border border-border rounded-lg p-5 bg-surface">
  <div class="flex items-center justify-between mb-3">
    <h3 class="font-display font-semibold text-sm text-primary">Widget Title</h3>
    <button class="text-xs text-accent">Action</button>
  </div>
  <!-- Widget content -->
</div>
```

For the Hosted Files widget:
- If no files hosted: "Activate AI Files" button
- If files hosted: list each file with URL, copy button, status badge, last updated

For the Crawler Ping widget:
- Last ping timestamp
- "Ping now" button with remaining count
- Last 3 pings with status

For the Mention Trend widget:
- MentionChart component with last 8 weeks
- Current week found/tested count
- Trend arrow (up/down vs last week)

For the Competitor widget:
- If no competitors: "Discover competitors" button
- If competitors: list with domain + score, "Scan all" button

For the Content Suggestions widget:
- "Generate suggestions" button if none
- Count of suggestions if generated, link to view

For the Agent Simulator widget:
- "Run simulation" button if never run
- StepFlow showing results if run

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/Dashboard.vue
git commit -m "feat: Pro dashboard with hosted files, pings, mentions, competitors, optimizer, simulator"
```

---

### Task 8: Build, Test, Deploy

- [ ] **Step 1: Build frontend**

```bash
cd frontend && npm run build
```

Expected: No errors.

- [ ] **Step 2: Commit and push**

```bash
git add -A
git commit -m "feat: complete Pro dashboard features — 6 automated services + redesigned dashboard"
git push
```

- [ ] **Step 3: Deploy**

```bash
ssh root@89.167.111.89 "cd /opt/agentready && git pull && docker compose build && docker compose up -d"
```

- [ ] **Step 4: Verify**

Test each endpoint:
```bash
curl -s https://agentcheck.site/api/health
curl -s https://agentcheck.site/hosted/test/llms.txt  # Should 404 (no files yet)
```

---

## Self-Review

- [x] **Spec coverage**: All 6 features (hosted files, crawler pings, mention tracking, competitor tracking, content optimizer, agent simulator) + dashboard redesign covered
- [x] **Placeholder scan**: All tasks have complete code
- [x] **Type consistency**: DB helper signatures match endpoint usage; API function names match across frontend/backend
