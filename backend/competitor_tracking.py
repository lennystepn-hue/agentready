import uuid
import json
import logging
from scanner.orchestrator import run_scan as execute_scan
from db import (
    save_competitor,
    get_competitors,
    update_competitor_score,
    get_scan,
    get_scan_insights,
    save_scan_insights,
    create_scan,
)
from ai_insights import generate_scan_insights

logger = logging.getLogger(__name__)


async def auto_discover_competitors(user_id: str, domain: str, scan_id: str) -> list[str]:
    cached = await get_scan_insights(scan_id)
    if cached and "competitors" in cached:
        return cached["competitors"][:3]

    scan = await get_scan(scan_id)
    if not scan or not scan.get("report_json"):
        return []

    report = json.loads(scan["report_json"])
    insights = await generate_scan_insights(domain, report)
    if "error" not in insights:
        await save_scan_insights(scan_id, insights)

    return insights.get("competitors", [])[:3]


async def scan_competitor(user_id: str, domain: str, competitor_domain: str) -> int | None:
    scan_id = str(uuid.uuid4())
    try:
        await create_scan(scan_id, competitor_domain, "system")
        await execute_scan(scan_id, competitor_domain)
        scan = await get_scan(scan_id)
        if scan and scan.get("total_score") is not None:
            score = scan["total_score"]
            # Look up the competitor record to get its id for the DB update
            competitors = await get_competitors(user_id, domain)
            for comp in competitors:
                if comp["competitor_domain"] == competitor_domain:
                    await update_competitor_score(comp["id"], score, scan_id)
                    break
            return score
    except Exception as e:
        logger.warning(f"Competitor scan failed for {competitor_domain}: {e}")
    return None
