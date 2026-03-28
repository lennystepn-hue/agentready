import json
import uuid
import logging
from contextlib import asynccontextmanager
from urllib.parse import urlparse

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from db import init_db, create_scan, get_scan, count_scans_today
from rate_limit import limiter
from scanner.orchestrator import run_scan

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    logger.info("Database initialized")
    yield


app = FastAPI(
    title="AgentReady - Agent Readiness Scanner",
    description="Scan e-commerce shops for AI agent readiness",
    version="1.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ScanRequest(BaseModel):
    domain: str

    @field_validator("domain")
    @classmethod
    def validate_domain(cls, v: str) -> str:
        v = v.strip().lower()
        # Strip protocol if provided
        if "://" in v:
            parsed = urlparse(v)
            v = parsed.netloc or parsed.path
        # Strip trailing slash and path
        v = v.split("/")[0]
        # Strip port for validation
        host = v.split(":")[0]
        if not host or "." not in host:
            raise ValueError("Invalid domain. Provide a valid domain like 'example.com'.")
        if len(host) > 253:
            raise ValueError("Domain too long.")
        return v


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "AgentReady Scanner"}


@app.post("/api/scan")
@limiter.limit("5/day")
async def start_scan(
    scan_request: ScanRequest,
    background_tasks: BackgroundTasks,
    request: Request,
):
    domain = scan_request.domain
    ip_address = request.client.host if request.client else "unknown"

    # Additional rate limit check via DB
    scans_today = await count_scans_today(ip_address)
    if scans_today >= 5:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Maximum 5 scans per day.",
        )

    scan_id = str(uuid.uuid4())

    await create_scan(scan_id, domain, ip_address)
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
