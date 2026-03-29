import io
import json
import re
import uuid
import logging
from dotenv import load_dotenv
load_dotenv()
import zipfile
from contextlib import asynccontextmanager
from urllib.parse import urlparse

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse, StreamingResponse
from pydantic import BaseModel, field_validator

from db import (
    init_db,
    create_scan,
    get_scan,
    delete_scan,
    count_scans_today,
    create_user,
    get_user_by_email,
    get_user_by_id,
    update_user_plan,
    user_has_fix_access,
    get_user_scans,
    add_user_id_to_scan,
    get_scan_history,
    get_user_monitors,
    create_monitor,
    delete_monitor,
    create_comparison,
    get_user_comparisons,
    get_scan_insights,
    save_scan_insights,
    get_hosted_files,
    get_hosted_file_by_token,
    get_crawler_pings,
    count_pings_today,
    get_mention_history,
    get_competitors,
    save_competitor,
    delete_competitor,
)
from scanner.orchestrator import run_scan
from fix_generator import generate_fixes
from auth import (
    hash_password,
    verify_password,
    create_token,
    get_current_user,
    get_optional_user,
)
from payments import create_checkout_session, handle_webhook_event
from monitoring import run_monitoring_cycle
from ai_discovery import run_discovery_test
from ai_insights import generate_scan_insights
from hosted_files import activate_hosted_files, refresh_hosted_files
from crawler_ping import ping_crawlers
from mention_tracking import track_mentions
from competitor_tracking import auto_discover_competitors, scan_competitor
from content_optimizer import optimize_content
from agent_simulator import run_simulation

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    logger.info("Database initialized")

    # Start background scheduler for weekly monitoring
    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler

        scheduler = AsyncIOScheduler()
        scheduler.add_job(run_monitoring_cycle, "interval", weeks=1, id="monitoring_cycle")
        scheduler.start()
        logger.info("Monitoring scheduler started (weekly cycle).")
    except Exception:
        logger.warning("Failed to start monitoring scheduler. Monitoring will not run automatically.")

    yield


app = FastAPI(
    title="AgentCheck - Agent Readiness Scanner",
    description="Scan e-commerce shops for AI agent readiness",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://agentcheck.site", "http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class ScanRequest(BaseModel):
    domain: str

    @field_validator("domain")
    @classmethod
    def validate_domain(cls, v: str) -> str:
        v = v.strip().lower()
        if "://" in v:
            parsed = urlparse(v)
            v = parsed.netloc or parsed.path
        v = v.split("/")[0]
        host = v.split(":")[0]
        if not host or "." not in host:
            raise ValueError("Invalid domain. Provide a valid domain like 'example.com'.")
        if len(host) > 253:
            raise ValueError("Domain too long.")
        return v


class RegisterRequest(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = v.strip().lower()
        if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", v):
            raise ValueError("Invalid email address.")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters.")
        return v


class LoginRequest(BaseModel):
    email: str
    password: str


class CheckoutRequest(BaseModel):
    price_type: str
    scan_id: str | None = None

    @field_validator("price_type")
    @classmethod
    def validate_price_type(cls, v: str) -> str:
        if v not in ("fix_files", "pro"):
            raise ValueError("price_type must be 'fix_files' or 'pro'.")
        return v


class MonitorRequest(BaseModel):
    domain: str

    @field_validator("domain")
    @classmethod
    def validate_domain(cls, v: str) -> str:
        v = v.strip().lower()
        if "://" in v:
            parsed = urlparse(v)
            v = parsed.netloc or parsed.path
        v = v.split("/")[0]
        host = v.split(":")[0]
        if not host or "." not in host:
            raise ValueError("Invalid domain.")
        return v


class CompareRequest(BaseModel):
    domains: list[str]

    @field_validator("domains")
    @classmethod
    def validate_domains(cls, v: list[str]) -> list[str]:
        if len(v) < 2:
            raise ValueError("At least 2 domains required for comparison.")
        if len(v) > 4:
            raise ValueError("Maximum 4 domains for comparison.")
        return v


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/.well-known/ucp")
async def ucp_endpoint():
    return {
        "version": "1.0",
        "business": {
            "name": "AgentCheck",
            "type": "saas",
            "description": "AI agent readiness scanner for any website",
            "url": "https://agentcheck.site",
            "languages": ["en"],
            "support_email": "contact@agentcheck.site"
        },
        "capabilities": {
            "website_scanning": True,
            "ai_readiness_scoring": True,
            "fix_generation": True,
            "competitor_comparison": True,
            "monitoring": True,
            "api_access": True
        },
        "endpoints": {
            "scan": "/api/scan",
            "health": "/api/health",
            "pricing": "/api/pricing"
        },
        "authentication": {
            "type": "bearer_token",
            "registration": "/api/auth/register"
        }
    }


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "AgentCheck Scanner"}


# ---------------------------------------------------------------------------
# Auth endpoints
# ---------------------------------------------------------------------------

@app.post("/api/auth/register")
async def register(body: RegisterRequest):
    email = body.email.strip().lower()
    existing = await get_user_by_email(email)
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered.")

    user_id = str(uuid.uuid4())
    hashed = hash_password(body.password)
    await create_user(user_id, email, hashed)

    token = create_token(user_id)
    return {
        "token": token,
        "user": {
            "id": user_id,
            "email": body.email,
            "plan": "free",
        },
    }


@app.post("/api/auth/login")
async def login(body: LoginRequest):
    user = await get_user_by_email(body.email.strip().lower())
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    if not verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    token = create_token(user["id"])
    return {
        "token": token,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "plan": user["plan"],
        },
    }


@app.get("/api/auth/me")
async def get_me(user: dict = Depends(get_current_user)):
    return {
        "id": user["id"],
        "email": user["email"],
        "plan": user["plan"],
        "created_at": user["created_at"],
    }


# ---------------------------------------------------------------------------
# Scan endpoints
# ---------------------------------------------------------------------------

@app.post("/api/scan")
async def start_scan(
    scan_request: ScanRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    user: dict | None = Depends(get_optional_user),
):
    domain = scan_request.domain
    ip_address = request.client.host if request.client else "unknown"

    # Additional rate limit check via DB
    scans_today = await count_scans_today(ip_address)
    if scans_today >= 100:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Maximum 5 scans per day.",
        )

    scan_id = str(uuid.uuid4())

    await create_scan(scan_id, domain, ip_address)

    # Link scan to user if authenticated
    if user:
        await add_user_id_to_scan(scan_id, user["id"])

    background_tasks.add_task(run_scan, scan_id, domain)

    logger.info(f"Scan {scan_id} started for {domain} from {ip_address}")

    return {
        "scan_id": scan_id,
        "status": "pending",
        "message": f"Scan started for {domain}. Poll GET /api/scan/{scan_id} for results.",
    }


@app.get("/api/scan/{scan_id}")
async def get_scan_result(scan_id: str):
    scan = await get_scan(scan_id)

    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found.")

    status = scan["status"]

    if status in ("pending", "running"):
        return {
            "scan_id": scan_id,
            "status": status,
            "message": "Scan is still in progress. Please poll again.",
        }

    if status == "error":
        error_detail = "Scan failed."
        if scan["report_json"]:
            try:
                report = json.loads(scan["report_json"])
                error_detail = report.get("error", error_detail)
            except json.JSONDecodeError:
                pass
        return {
            "scan_id": scan_id,
            "status": "error",
            "message": error_detail,
        }

    # Completed scan
    report = {}
    if scan["report_json"]:
        try:
            report = json.loads(scan["report_json"])
        except json.JSONDecodeError:
            pass

    return {
        "scan_id": scan_id,
        "status": "completed",
        "domain": scan["domain"],
        "total_score": scan["total_score"],
        "grade": scan["grade"],
        "report": report,
    }


# ---------------------------------------------------------------------------
# Fix files endpoints (gated)
# ---------------------------------------------------------------------------

@app.get("/api/scan/{scan_id}/fixes")
async def get_fix_files(
    scan_id: str,
    user: dict | None = Depends(get_optional_user),
):
    scan = await get_scan(scan_id)

    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found.")

    if scan["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Scan is not completed (status: {scan['status']}). Fix files can only be generated for completed scans.",
        )

    # Check access: user must be authenticated and have fix access
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Authentication required to access fix files. Purchase fix files or upgrade to Pro.",
        )

    has_access = await user_has_fix_access(user["id"], scan_id)
    if not has_access:
        raise HTTPException(
            status_code=403,
            detail="Fix file access required. Purchase fix files for this scan or upgrade to Pro.",
        )

    try:
        result = await generate_fixes(scan_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return result


@app.get("/api/scan/{scan_id}/fixes/download")
async def download_fix_files(
    scan_id: str,
    user: dict | None = Depends(get_optional_user),
):
    scan = await get_scan(scan_id)

    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found.")

    if scan["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Scan is not completed (status: {scan['status']}). Fix files can only be generated for completed scans.",
        )

    # Check access
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Authentication required to download fix files.",
        )

    has_access = await user_has_fix_access(user["id"], scan_id)
    if not has_access:
        raise HTTPException(
            status_code=403,
            detail="Fix file access required. Purchase fix files for this scan or upgrade to Pro.",
        )

    try:
        result = await generate_fixes(scan_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Create in-memory ZIP file
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_info in result["files"]:
            zf.writestr(file_info["name"], file_info["content"])

    zip_buffer.seek(0)
    domain = result["domain"]
    filename = f"agentcheck-fixes-{domain}.zip"

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/api/scan/{scan_id}/access")
async def check_scan_access(
    scan_id: str,
    user: dict = Depends(get_current_user),
):
    """Returns access info for a scan."""
    has_access = await user_has_fix_access(user["id"], scan_id)
    return {
        "has_fix_access": has_access,
        "plan": user["plan"],
    }


# ---------------------------------------------------------------------------
# Payments
# ---------------------------------------------------------------------------

@app.post("/api/checkout/session")
async def create_checkout(
    body: CheckoutRequest,
    user: dict = Depends(get_current_user),
):
    try:
        checkout_url = await create_checkout_session(
            user_id=user["id"],
            user_email=user["email"],
            price_type=body.price_type,
            scan_id=body.scan_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"checkout_url": checkout_url}


@app.post("/api/billing/portal")
async def create_billing_portal(user: dict = Depends(get_current_user)):
    """Creates a Stripe Billing Portal session for subscription management."""
    import stripe
    import os
    stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")

    user_data = await get_user_by_id(user["id"])
    if not user_data or not user_data.get("stripe_customer_id"):
        raise HTTPException(status_code=400, detail="No active subscription found.")

    session = stripe.billing_portal.Session.create(
        customer=user_data["stripe_customer_id"],
        return_url=os.environ.get("FRONTEND_URL", "http://localhost:5173") + "/dashboard",
    )
    return {"portal_url": session.url}


@app.post("/api/stripe/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        await handle_webhook_event(payload, sig_header)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Monitoring (Pro only)
# ---------------------------------------------------------------------------

@app.get("/api/monitoring")
async def list_monitors(user: dict = Depends(get_current_user)):
    if user["plan"] != "pro":
        raise HTTPException(status_code=403, detail="Pro plan required for monitoring.")
    monitors = await get_user_monitors(user["id"])
    return {"monitors": monitors}


@app.post("/api/monitoring")
async def add_monitor(
    body: MonitorRequest,
    user: dict = Depends(get_current_user),
):
    if user["plan"] != "pro":
        raise HTTPException(status_code=403, detail="Pro plan required for monitoring.")

    monitor_id = str(uuid.uuid4())
    await create_monitor(monitor_id, user["id"], body.domain, user["email"])
    return {"id": monitor_id, "domain": body.domain, "message": "Monitor added."}


@app.delete("/api/monitoring/{monitor_id}")
async def remove_monitor(
    monitor_id: str,
    user: dict = Depends(get_current_user),
):
    if user["plan"] != "pro":
        raise HTTPException(status_code=403, detail="Pro plan required for monitoring.")

    await delete_monitor(monitor_id, user["id"])
    return {"message": "Monitor removed."}


# ---------------------------------------------------------------------------
# Competitor Compare (Pro only)
# ---------------------------------------------------------------------------

@app.post("/api/compare")
async def compare_domains(
    body: CompareRequest,
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user),
):
    if user["plan"] != "pro":
        raise HTTPException(status_code=403, detail="Pro plan required for competitor comparison.")

    comp_id = str(uuid.uuid4())
    scan_ids = []

    for domain in body.domains:
        # Normalize domain
        domain = domain.strip().lower()
        if "://" in domain:
            parsed = urlparse(domain)
            domain = parsed.netloc or parsed.path
        domain = domain.split("/")[0]

        scan_id = str(uuid.uuid4())
        await create_scan(scan_id, domain, "compare")
        await add_user_id_to_scan(scan_id, user["id"])
        scan_ids.append({"domain": domain, "scan_id": scan_id})
        background_tasks.add_task(run_scan, scan_id, domain)

    await create_comparison(
        comp_id=comp_id,
        user_id=user["id"],
        domains_json=json.dumps(body.domains),
        results_json=json.dumps(scan_ids),
    )

    return {
        "comparison_id": comp_id,
        "scans": scan_ids,
        "message": "Comparison scans started. Poll each scan_id for results.",
    }


# ---------------------------------------------------------------------------
# Score History (Pro only)
# ---------------------------------------------------------------------------

@app.get("/api/history/{domain}")
async def domain_history(
    domain: str,
    user: dict = Depends(get_current_user),
):
    if user["plan"] != "pro":
        raise HTTPException(status_code=403, detail="Pro plan required for score history.")

    history = await get_scan_history(domain, user["id"])
    return {"domain": domain, "history": history}


# ---------------------------------------------------------------------------
# User scans
# ---------------------------------------------------------------------------

@app.get("/api/user/scans")
async def list_user_scans(user: dict = Depends(get_current_user)):
    scans = await get_user_scans(user["id"])
    return {"scans": scans}


@app.delete("/api/scan/{scan_id}")
async def delete_user_scan(scan_id: str, user: dict = Depends(get_current_user)):
    """Delete a scan. Only the scan owner can delete it."""
    deleted = await delete_scan(scan_id, user["id"])
    if not deleted:
        raise HTTPException(status_code=404, detail="Scan not found or not yours.")
    return {"status": "deleted"}


# ---------------------------------------------------------------------------
# Pricing (public)
# ---------------------------------------------------------------------------

@app.get("/api/pricing")
async def get_pricing():
    return {
        "plans": [
            {
                "id": "free",
                "name": "Free",
                "price": 0,
                "features": ["Scan + Score", "Generic fix suggestions"],
            },
            {
                "id": "one-time",
                "name": "Fix Files",
                "price": 9,
                "currency": "USD",
                "features": [
                    "Everything in Free",
                    "Tailored fix files (1 scan)",
                    "ZIP download",
                ],
            },
            {
                "id": "pro",
                "name": "Pro",
                "price": 29,
                "currency": "USD",
                "interval": "month",
                "features": [
                    "Everything in Fix Files",
                    "Unlimited fix generation",
                    "Weekly monitoring",
                    "Competitor compare",
                    "Score history",
                ],
            },
        ]
    }


# ---------------------------------------------------------------------------
# AI Insights (Pro only)
# ---------------------------------------------------------------------------

@app.get("/api/scan/{scan_id}/insights")
async def get_insights(scan_id: str, user: dict = Depends(get_current_user)):
    """Get AI-powered insights for a scan. Pro feature. Results are cached."""
    user_data = await get_user_by_id(user["id"])
    if not user_data or user_data.get("plan") != "pro":
        raise HTTPException(status_code=403, detail="AI Insights is a Pro feature.")

    scan = await get_scan(scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found.")
    if scan["status"] != "completed":
        raise HTTPException(status_code=400, detail="Scan must be completed.")

    # Check cache first
    cached = await get_scan_insights(scan_id)
    if cached and "error" not in cached:
        return {"insights": cached, "cached": True}

    # Generate new insights
    report = {}
    if scan.get("report_json"):
        try:
            report = json.loads(scan["report_json"])
        except:
            pass

    insights = await generate_scan_insights(scan["domain"], report)

    # Cache if successful
    if "error" not in insights:
        await save_scan_insights(scan_id, insights)

    return {"insights": insights, "cached": False}


# ---------------------------------------------------------------------------
# Hosted Files (Pro only)
# ---------------------------------------------------------------------------

class ActivateHostedFilesRequest(BaseModel):
    domain: str
    scan_id: str


@app.post("/api/hosted-files/activate")
async def activate_hosted(
    body: ActivateHostedFilesRequest,
    user: dict = Depends(get_current_user),
):
    """Generate and host AI files for a domain. Pro only."""
    if user["plan"] != "pro":
        raise HTTPException(status_code=403, detail="Pro plan required for hosted files.")

    scan = await get_scan(body.scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found.")
    if scan["status"] != "completed":
        raise HTTPException(status_code=400, detail="Scan must be completed.")

    # Check if files already exist — refresh instead
    existing = await get_hosted_files(user["id"], body.domain)
    if existing:
        files = await refresh_hosted_files(user["id"], body.domain, body.scan_id)
    else:
        files = await activate_hosted_files(user["id"], body.domain, body.scan_id)

    return {"files": files}


@app.get("/api/hosted-files")
async def list_hosted_files(
    user: dict = Depends(get_current_user),
    domain: str | None = None,
):
    """List user's hosted files, optionally filtered by domain."""
    files = await get_hosted_files(user["id"], domain)
    return {"files": files}


@app.get("/hosted/{token}/{filename}")
async def serve_hosted_file(token: str, filename: str):
    """Public endpoint — serves hosted file content as plain text. No auth required."""
    file_type = filename  # filename is the file_type, e.g. "ai.txt"
    record = await get_hosted_file_by_token(token, file_type)
    if not record:
        raise HTTPException(status_code=404, detail="File not found.")

    return PlainTextResponse(
        content=record["content"],
        headers={"Cache-Control": "public, max-age=3600"},
    )


# ---------------------------------------------------------------------------
# AI Discovery Test
# ---------------------------------------------------------------------------

@app.post("/api/scan/{scan_id}/discovery")
async def run_ai_discovery(scan_id: str, user: dict = Depends(get_current_user)):
    """Run AI discovery test for a completed scan. Pro feature."""
    user_data = await get_user_by_id(user["id"])
    if not user_data or user_data.get("plan") != "pro":
        raise HTTPException(status_code=403, detail="AI Discovery Test is a Pro feature.")

    scan = await get_scan(scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found.")
    if scan["status"] != "completed":
        raise HTTPException(status_code=400, detail="Scan must be completed first.")

    # Extract site type and hints from scan results
    product_hints = []
    site_type = "generic"
    if scan.get("report_json"):
        try:
            report = json.loads(scan["report_json"])
            site_type = report.get("site_type", "generic")
        except:
            pass

    result = await run_discovery_test(scan["domain"], product_hints, site_type)
    return result


@app.post("/api/discovery/quick")
async def quick_discovery(body: ScanRequest):
    """Quick discovery test (limited, no auth needed)."""
    domain = body.domain
    result = await run_discovery_test(domain)
    # Only return summary for free users
    return {
        "domain": result["domain"],
        "discovery_score": result["discovery_score"],
        "summary": result["summary"],
        "queries_tested": result["queries_tested"],
        "queries_found": result["queries_found"],
        # Don't include detailed results for free
    }


# ---------------------------------------------------------------------------
# Crawler Pings (Pro only)
# ---------------------------------------------------------------------------

class CrawlerPingRequest(BaseModel):
    domain: str

    @field_validator("domain")
    @classmethod
    def validate_domain(cls, v: str) -> str:
        v = v.strip().lower()
        if "://" in v:
            parsed = urlparse(v)
            v = parsed.netloc or parsed.path
        v = v.split("/")[0]
        host = v.split(":")[0]
        if not host or "." not in host:
            raise ValueError("Invalid domain.")
        return v


@app.post("/api/crawler-ping")
async def manual_crawler_ping(
    user: dict = Depends(get_current_user),
):
    """Manually ping AI crawlers and search engines about content updates. Pro only, max 3/day."""
    if user["plan"] != "pro":
        raise HTTPException(status_code=403, detail="Pro plan required for crawler pings.")

    pings_today = await count_pings_today(user["id"])
    if pings_today >= 3:
        raise HTTPException(status_code=429, detail="Maximum 3 manual pings per day.")

    # Use domain from latest scan
    scans = await get_user_scans(user["id"], limit=1)
    if not scans:
        raise HTTPException(status_code=400, detail="No scans found. Run a scan first.")
    domain = scans[0]["domain"]

    results = await ping_crawlers(user["id"], domain, manual=True)
    return {"domain": domain, "results": results, "remaining_today": 2 - pings_today}


@app.get("/api/crawler-ping/history")
async def crawler_ping_history(user: dict = Depends(get_current_user)):
    """Get last 20 crawler pings. Pro only."""
    if user["plan"] != "pro":
        raise HTTPException(status_code=403, detail="Pro plan required for crawler pings.")

    pings = await get_crawler_pings(user["id"], limit=20)
    return {"pings": pings}


# ---------------------------------------------------------------------------
# Mention Tracking (Pro only)
# ---------------------------------------------------------------------------

@app.get("/api/mentions/{domain}")
async def mention_history(domain: str, user: dict = Depends(get_current_user)):
    """Get mention tracking history for a domain. Pro only."""
    if user["plan"] != "pro":
        raise HTTPException(status_code=403, detail="Pro plan required for mention tracking.")

    history = await get_mention_history(user["id"], domain)
    return {"domain": domain, "history": history}


@app.post("/api/mentions/{domain}/track")
async def run_mention_tracking(domain: str, user: dict = Depends(get_current_user)):
    """Run mention tracking for a domain now. Pro only."""
    if user["plan"] != "pro":
        raise HTTPException(status_code=403, detail="Pro plan required for mention tracking.")

    result = await track_mentions(user["id"], domain)
    return result


# ---------------------------------------------------------------------------
# Competitor Tracking (Pro only)
# ---------------------------------------------------------------------------

@app.get("/api/competitors/{domain}")
async def list_competitors(domain: str, user: dict = Depends(get_current_user)):
    """List tracked competitors for a domain. Pro only."""
    if user["plan"] != "pro":
        raise HTTPException(status_code=403, detail="Pro plan required for competitor tracking.")

    competitors = await get_competitors(user["id"], domain)
    return {"domain": domain, "competitors": competitors}


class DiscoverCompetitorsRequest(BaseModel):
    scan_id: str


@app.post("/api/competitors/{domain}/discover")
async def discover_competitors(
    domain: str,
    body: DiscoverCompetitorsRequest,
    user: dict = Depends(get_current_user),
):
    """AI-discover competitors from scan insights. Pro only."""
    if user["plan"] != "pro":
        raise HTTPException(status_code=403, detail="Pro plan required for competitor tracking.")

    discovered = await auto_discover_competitors(user["id"], domain, body.scan_id)

    # Save any newly discovered competitors
    existing = await get_competitors(user["id"], domain)
    existing_domains = {c["competitor_domain"] for c in existing}
    added = []
    for comp_domain in discovered:
        if comp_domain not in existing_domains:
            comp_id = str(uuid.uuid4())
            await save_competitor(comp_id, user["id"], domain, comp_domain)
            added.append(comp_domain)

    return {"domain": domain, "discovered": discovered, "added": added}


@app.post("/api/competitors/{domain}/scan")
async def scan_competitors(
    domain: str,
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user),
):
    """Scan all tracked competitors (max 3). Pro only."""
    if user["plan"] != "pro":
        raise HTTPException(status_code=403, detail="Pro plan required for competitor tracking.")

    competitors = await get_competitors(user["id"], domain)
    if not competitors:
        raise HTTPException(status_code=404, detail="No competitors tracked for this domain.")

    # Limit to 3 competitors
    to_scan = competitors[:3]
    results = []
    for comp in to_scan:
        score = await scan_competitor(user["id"], domain, comp["competitor_domain"])
        results.append({
            "competitor": comp["competitor_domain"],
            "score": score,
        })

    return {"domain": domain, "results": results}


@app.delete("/api/competitors/{domain}/{competitor}")
async def remove_competitor(
    domain: str,
    competitor: str,
    user: dict = Depends(get_current_user),
):
    """Remove a tracked competitor. Pro only."""
    if user["plan"] != "pro":
        raise HTTPException(status_code=403, detail="Pro plan required for competitor tracking.")

    # Find the competitor record to get its id
    competitors = await get_competitors(user["id"], domain)
    comp_record = None
    for c in competitors:
        if c["competitor_domain"] == competitor:
            comp_record = c
            break

    if not comp_record:
        raise HTTPException(status_code=404, detail="Competitor not found.")

    await delete_competitor(comp_record["id"], user["id"])
    return {"message": f"Competitor {competitor} removed."}


# ---------------------------------------------------------------------------
# Content Optimizer (Pro only)
# ---------------------------------------------------------------------------

@app.post("/api/content-optimize/{scan_id}")
async def content_optimize(scan_id: str, user: dict = Depends(get_current_user)):
    """GPT-powered content optimization suggestions. Pro only. Cached."""
    user_data = await get_user_by_id(user["id"])
    if not user_data or user_data.get("plan") != "pro":
        raise HTTPException(status_code=403, detail="Content optimization is a Pro feature.")

    scan = await get_scan(scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found.")
    if scan["status"] != "completed":
        raise HTTPException(status_code=400, detail="Scan must be completed.")

    result = await optimize_content(user["id"], scan_id)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    return result


# ---------------------------------------------------------------------------
# Agent Simulator (Pro only)
# ---------------------------------------------------------------------------

@app.post("/api/simulate/{scan_id}")
async def simulate_agent(scan_id: str, user: dict = Depends(get_current_user)):
    """Simulate an AI agent navigating the site step by step. Pro only. Cached."""
    user_data = await get_user_by_id(user["id"])
    if not user_data or user_data.get("plan") != "pro":
        raise HTTPException(status_code=403, detail="Agent simulation is a Pro feature.")

    scan = await get_scan(scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found.")
    if scan["status"] != "completed":
        raise HTTPException(status_code=400, detail="Scan must be completed.")

    result = await run_simulation(user["id"], scan_id)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    return result


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
