import json
import logging
import re
import uuid

import httpx

from db import get_scan, save_agent_simulation, get_agent_simulation

logger = logging.getLogger(__name__)

USER_AGENT = "Mozilla/5.0 (compatible; AgentCheck/1.0; +https://agentcheck.site)"

STEPS_BY_TYPE = {
    "ecommerce": [
        {
            "name": "homepage",
            "description": "Load homepage",
            "check": lambda html: len(html) > 500,
            "indicators": [],
        },
        {
            "name": "product_listing",
            "description": "Find product listing page",
            "check": None,
            "indicators": [
                r'href=["\'][^"\']*(?:products|shop|catalog|collection|category)[^"\']*["\']',
                r'(?:product|item|shop|store|catalog)',
            ],
        },
        {
            "name": "product_details",
            "description": "Find product details page",
            "check": None,
            "indicators": [
                r'href=["\'][^"\']*(?:product/|item/|p/)[^"\']*["\']',
                r'(?:price|add.to.cart|buy.now|product.name|product.description)',
            ],
        },
        {
            "name": "price_check",
            "description": "Verify price is machine-readable",
            "check": None,
            "indicators": [
                r'(?:price|amount|cost)[\s"\'=:]+[\s"\']*[\$\€\£]?\s*\d+[\.,]\d{2}',
                r'"price"\s*:', r'itemprop=["\']price["\']',
                r'class=["\'][^"\']*price[^"\']*["\']',
            ],
        },
        {
            "name": "checkout",
            "description": "Find checkout/cart flow",
            "check": None,
            "indicators": [
                r'href=["\'][^"\']*(?:cart|checkout|basket)[^"\']*["\']',
                r'(?:add.to.cart|checkout|view.cart|shopping.bag)',
            ],
        },
    ],
    "blog": [
        {
            "name": "homepage",
            "description": "Load homepage",
            "check": lambda html: len(html) > 500,
            "indicators": [],
        },
        {
            "name": "article_listing",
            "description": "Find article listing page",
            "check": None,
            "indicators": [
                r'href=["\'][^"\']*(?:blog|articles|posts|news|stories)[^"\']*["\']',
                r'(?:latest.posts|recent.articles|blog|news)',
            ],
        },
        {
            "name": "article_content",
            "description": "Find article content structure",
            "check": None,
            "indicators": [
                r'<article',
                r'class=["\'][^"\']*(?:post|article|entry|content)[^"\']*["\']',
                r'(?:read.more|continue.reading|full.story)',
            ],
        },
        {
            "name": "author_info",
            "description": "Find author information",
            "check": None,
            "indicators": [
                r'(?:author|written.by|posted.by|byline)',
                r'rel=["\']author["\']',
                r'class=["\'][^"\']*author[^"\']*["\']',
            ],
        },
        {
            "name": "rss_feed",
            "description": "Find RSS/Atom feed",
            "check": None,
            "indicators": [
                r'type=["\']application/(?:rss|atom)\+xml["\']',
                r'href=["\'][^"\']*(?:feed|rss|atom)[^"\']*["\']',
                r'/feed', r'/rss',
            ],
        },
    ],
    "saas": [
        {
            "name": "homepage",
            "description": "Load homepage",
            "check": lambda html: len(html) > 500,
            "indicators": [],
        },
        {
            "name": "pricing",
            "description": "Find pricing page",
            "check": None,
            "indicators": [
                r'href=["\'][^"\']*pric[^"\']*["\']',
                r'(?:pricing|plans|packages|subscription)',
            ],
        },
        {
            "name": "features",
            "description": "Find features page",
            "check": None,
            "indicators": [
                r'href=["\'][^"\']*feature[^"\']*["\']',
                r'(?:features|capabilities|what.we.offer|solutions)',
            ],
        },
        {
            "name": "signup_demo",
            "description": "Find signup or demo page",
            "check": None,
            "indicators": [
                r'href=["\'][^"\']*(?:sign.?up|register|demo|trial|get.started)[^"\']*["\']',
                r'(?:sign.up|get.started|free.trial|request.demo|start.free)',
            ],
        },
        {
            "name": "docs",
            "description": "Find documentation",
            "check": None,
            "indicators": [
                r'href=["\'][^"\']*(?:docs|documentation|help|support|knowledge|api)[^"\']*["\']',
                r'(?:documentation|help.center|knowledge.base|api.reference|developer)',
            ],
        },
    ],
    "restaurant": [
        {
            "name": "homepage",
            "description": "Load homepage",
            "check": lambda html: len(html) > 500,
            "indicators": [],
        },
        {
            "name": "menu",
            "description": "Find menu page",
            "check": None,
            "indicators": [
                r'href=["\'][^"\']*menu[^"\']*["\']',
                r'(?:our.menu|food.menu|menu|dishes|specials)',
            ],
        },
        {
            "name": "hours",
            "description": "Find opening hours",
            "check": None,
            "indicators": [
                r'(?:opening.hours|business.hours|hours.of.operation|we.are.open|open.daily)',
                r'(?:mon|tue|wed|thu|fri|sat|sun)(?:day)?.*\d{1,2}[:.]\d{2}',
                r'itemprop=["\']openingHours["\']',
            ],
        },
        {
            "name": "reservation",
            "description": "Find reservation system",
            "check": None,
            "indicators": [
                r'href=["\'][^"\']*(?:reserv|book)[^"\']*["\']',
                r'(?:reservation|book.a.table|make.a.booking|reserve|opentable)',
            ],
        },
        {
            "name": "location",
            "description": "Find location/address",
            "check": None,
            "indicators": [
                r'(?:address|location|find.us|visit.us|directions|get.directions)',
                r'(?:street|avenue|blvd|road|drive|lane|way)\b.*\d{5}',
                r'itemprop=["\']address["\']',
                r'(?:google.maps|maps\.google)',
            ],
        },
    ],
}


def _check_indicators(html: str, indicators: list[str]) -> tuple[bool, str]:
    """Check if any indicators match in the HTML. Returns (matched, detail)."""
    html_lower = html.lower()
    matched = []
    for pattern in indicators:
        try:
            if re.search(pattern, html_lower, re.IGNORECASE):
                matched.append(pattern)
        except re.error:
            continue
    if matched:
        return True, f"Found {len(matched)}/{len(indicators)} expected patterns"
    return False, f"No matching patterns found (checked {len(indicators)} patterns)"


async def run_simulation(user_id: str, scan_id: str) -> dict:
    """
    Simulate an AI agent navigating the site step by step.
    Site-type-aware. Caches results in agent_simulations table.
    """
    # Check cache
    cached = await get_agent_simulation(scan_id)
    if cached and cached.get("steps_json"):
        try:
            steps = json.loads(cached["steps_json"])
            return {
                "domain": cached.get("site_type", "generic"),
                "site_type": cached.get("site_type", "generic"),
                "steps": steps,
                "completed": cached.get("completed_steps", 0),
                "total": cached.get("total_steps", 0),
                "completion_rate": round(
                    (cached.get("completed_steps", 0) / max(cached.get("total_steps", 1), 1)) * 100
                ),
                "cached": True,
            }
        except (json.JSONDecodeError, TypeError):
            pass

    # Load scan
    scan = await get_scan(scan_id)
    if not scan:
        return {"error": "Scan not found"}
    if scan["status"] != "completed":
        return {"error": "Scan must be completed"}

    report = {}
    if scan.get("report_json"):
        try:
            report = json.loads(scan["report_json"])
        except json.JSONDecodeError:
            return {"error": "Could not parse scan report"}

    domain = scan["domain"]
    site_type = report.get("site_type", "generic")

    # Get steps for site type, fall back to generic ecommerce-style
    step_defs = STEPS_BY_TYPE.get(site_type, STEPS_BY_TYPE["ecommerce"])

    url = f"https://{domain}"
    steps_result = []
    blocked = False
    html = ""

    for step_def in step_defs:
        step_name = step_def["name"]
        description = step_def["description"]

        if blocked:
            steps_result.append({
                "name": step_name,
                "description": description,
                "status": "blocked",
                "detail": "Blocked by previous step failure",
            })
            continue

        if step_name == "homepage":
            # Actually fetch the homepage
            try:
                async with httpx.AsyncClient(
                    timeout=12,
                    follow_redirects=True,
                    headers={"User-Agent": USER_AGENT},
                ) as client:
                    resp = await client.get(url)
                    if resp.status_code == 200:
                        html = resp.text
                        if step_def["check"] and step_def["check"](html):
                            steps_result.append({
                                "name": step_name,
                                "description": description,
                                "status": "pass",
                                "detail": f"Homepage loaded successfully ({len(html)} bytes)",
                            })
                        elif step_def["check"]:
                            steps_result.append({
                                "name": step_name,
                                "description": description,
                                "status": "fail",
                                "detail": f"Homepage content too small ({len(html)} bytes)",
                            })
                            blocked = True
                        else:
                            steps_result.append({
                                "name": step_name,
                                "description": description,
                                "status": "pass",
                                "detail": f"Homepage loaded ({len(html)} bytes)",
                            })
                    else:
                        steps_result.append({
                            "name": step_name,
                            "description": description,
                            "status": "fail",
                            "detail": f"HTTP {resp.status_code} — could not load homepage",
                        })
                        blocked = True
            except httpx.TimeoutException:
                steps_result.append({
                    "name": step_name,
                    "description": description,
                    "status": "fail",
                    "detail": "Homepage request timed out (12s)",
                })
                blocked = True
            except Exception as e:
                steps_result.append({
                    "name": step_name,
                    "description": description,
                    "status": "fail",
                    "detail": f"Failed to fetch homepage: {str(e)[:100]}",
                })
                blocked = True
        else:
            # Check indicators in the fetched HTML
            indicators = step_def.get("indicators", [])
            if not indicators:
                steps_result.append({
                    "name": step_name,
                    "description": description,
                    "status": "pass",
                    "detail": "No specific indicators to check",
                })
                continue

            found, detail = _check_indicators(html, indicators)
            if found:
                steps_result.append({
                    "name": step_name,
                    "description": description,
                    "status": "pass",
                    "detail": detail,
                })
            else:
                steps_result.append({
                    "name": step_name,
                    "description": description,
                    "status": "fail",
                    "detail": detail,
                })
                blocked = True

    completed = sum(1 for s in steps_result if s["status"] == "pass")
    total = len(steps_result)
    completion_rate = round((completed / max(total, 1)) * 100)

    result = {
        "domain": domain,
        "site_type": site_type,
        "steps": steps_result,
        "completed": completed,
        "total": total,
        "completion_rate": completion_rate,
    }

    # Cache in DB
    try:
        sim_id = str(uuid.uuid4())
        await save_agent_simulation(
            sim_id, user_id, scan_id, site_type,
            json.dumps(steps_result), completed, total,
        )
    except Exception as e:
        logger.warning(f"Failed to cache simulation: {e}")

    return result
