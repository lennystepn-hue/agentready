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
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, field_validator

from db import (
    init_db,
    create_scan,
    get_scan,
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

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "AgentCheck Scanner"}


# ---------------------------------------------------------------------------
# Auth endpoints
# ---------------------------------------------------------------------------

@app.post("/api/auth/register")
async def register(body: RegisterRequest):
    existing = await get_user_by_email(body.email)
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered.")

    user_id = str(uuid.uuid4())
    hashed = hash_password(body.password)
    await create_user(user_id, body.email, hashed)

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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
