import os
import json
import logging
import httpx
import uuid

from db import save_content_suggestions, get_content_suggestions, get_scan

logger = logging.getLogger(__name__)
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")


SITE_TYPE_FOCUS = {
    "ecommerce": "product pages, buying intent, pricing clarity, and shopping experience",
    "blog": "article discoverability, author authority, content freshness, and topic relevance",
    "saas": "value proposition clarity, feature communication, pricing transparency, and conversion flow",
    "restaurant": "menu accessibility, location/hours clarity, reservation ease, and local SEO",
    "local_business": "service descriptions, contact info, service area clarity, and trust signals",
    "professional_service": "expertise communication, credentials, case studies, and client trust signals",
    "portfolio": "work showcase, skills communication, client testimonials, and contact accessibility",
    "generic": "content clarity, navigation, value proposition, and user engagement",
}


async def optimize_content(user_id: str, scan_id: str) -> dict:
    """
    GPT-powered content optimization suggestions for a completed scan.
    Caches results in the content_suggestions table.
    """
    # Check cache first
    cached = await get_content_suggestions(scan_id)
    if cached and cached.get("suggestions_json"):
        try:
            return json.loads(cached["suggestions_json"])
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

    if not OPENAI_API_KEY:
        return {"error": "OpenAI API key not configured"}

    domain = scan["domain"]
    site_type = report.get("site_type", "generic")
    site_label = report.get("site_label", "Website")
    checks = report.get("checks", [])

    # Extract current content signals from checks
    current_title = ""
    current_meta_desc = ""
    current_h1 = ""
    for check in checks:
        detail = check.get("detail", "")
        name = check.get("name", "").lower()
        if "title" in name and "found" in detail.lower():
            current_title = detail
        if "meta description" in name and "found" in detail.lower():
            current_meta_desc = detail
        if "h1" in name and "found" in detail.lower():
            current_h1 = detail

    focus = SITE_TYPE_FOCUS.get(site_type, SITE_TYPE_FOCUS["generic"])

    prompt = f"""You are an AI content optimization expert specializing in {focus}.

Analyze the homepage content for {domain} (a {site_label}).

Current signals detected:
- Title: {current_title or 'Not clearly detected'}
- Meta description: {current_meta_desc or 'Not clearly detected'}
- H1: {current_h1 or 'Not clearly detected'}
- Site type: {site_label}
- Score: {report.get('total_score', 0)}/100

Suggest optimized versions of these elements for better AI agent readability and discoverability.

Respond in this exact JSON format:
{{
  "suggestions": [
    {{
      "element": "title",
      "current": "current title or best guess",
      "suggested": "your optimized version",
      "reason": "why this is better for AI agents"
    }},
    {{
      "element": "meta_description",
      "current": "current meta description or best guess",
      "suggested": "your optimized version (max 160 chars)",
      "reason": "why this is better for AI agents"
    }},
    {{
      "element": "h1",
      "current": "current H1 or best guess",
      "suggested": "your optimized version",
      "reason": "why this is better for AI agents"
    }},
    {{
      "element": "key_paragraph",
      "current": "inferred key paragraph topic",
      "suggested": "a concise introductory paragraph optimized for AI consumption",
      "reason": "why this helps AI agents understand the site"
    }}
  ],
  "general_tips": [
    "Tip 1 specific to this {site_label.lower()}",
    "Tip 2 specific to this {site_label.lower()}",
    "Tip 3 specific to this {site_label.lower()}"
  ]
}}

Be specific to {domain} and the {site_label.lower()} category. Make suggestions actionable and realistic."""

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json",
                },
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
                content = data["choices"][0]["message"]["content"]
                result = json.loads(content)

                # Cache in DB
                suggestion_id = str(uuid.uuid4())
                await save_content_suggestions(
                    suggestion_id, user_id, scan_id, json.dumps(result)
                )

                return result
            else:
                logger.warning(f"OpenAI API error: {resp.status_code} {resp.text[:200]}")
                return {"error": f"AI service unavailable (HTTP {resp.status_code})"}
    except Exception as e:
        logger.warning(f"Content optimization failed: {e}")
        return {"error": str(e)[:200]}
