import uuid
import json
import logging
from datetime import datetime, timezone
from ai_discovery import run_discovery_test
from db import save_mention_record

logger = logging.getLogger(__name__)


async def track_mentions(user_id: str, domain: str, site_type: str = "generic") -> dict:
    result = await run_discovery_test(domain, site_type=site_type)
    week_date = datetime.now(timezone.utc).strftime("%Y-W%W")
    record_id = str(uuid.uuid4())
    await save_mention_record(
        record_id, user_id, domain, week_date,
        result.get("queries_tested", 0),
        result.get("queries_found", 0),
        json.dumps(result.get("results", [])),
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
