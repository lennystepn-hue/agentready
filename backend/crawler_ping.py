import uuid
import logging
import httpx
from db import save_crawler_ping, count_pings_today

logger = logging.getLogger(__name__)


async def ping_crawlers(user_id: str, domain: str, manual: bool = False) -> list[dict]:
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

    return results
