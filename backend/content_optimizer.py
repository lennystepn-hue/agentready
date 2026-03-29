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

    # Extract actual check messages to give GPT real context
    check_summaries = []
    for check in checks[:10]:
        check_summaries.append(f"- {check.get('name', '?')}: {check.get('status', '?')} — {check.get('message', '')[:100]}")
    checks_text = "\n".join(check_summaries) if check_summaries else "No detailed check data available."

    # Get AI insights if cached (they contain market_segment, competitors etc)
    insights_context = ""
    if report.get("ai_insights_json"):
        try:
            insights = json.loads(report["ai_insights_json"]) if isinstance(report.get("ai_insights_json"), str) else {}
            if insights.get("market_segment"):
                insights_context = f"\nMarket segment: {insights['market_segment']}"
            if insights.get("competitors"):
                insights_context += f"\nCompetitors: {', '.join(insights['competitors'][:3])}"
        except:
            pass

    # Check for cached insights in the scan row
    scan_insights = scan.get("ai_insights_json", "")
    if scan_insights and not insights_context:
        try:
            ins = json.loads(scan_insights)
            if ins.get("market_segment"):
                insights_context = f"\nMarket segment: {ins['market_segment']}"
            if ins.get("visibility_summary"):
                insights_context += f"\nAI visibility: {ins['visibility_summary'][:200]}"
        except:
            pass

    prompt = f"""You are an AI visibility optimization expert. Your job is to suggest content improvements that make a website more likely to be found and recommended by AI agents (ChatGPT, Claude, Gemini, Perplexity).

IMPORTANT: You must analyze the ACTUAL website at {domain}. Do NOT guess what the site does based on the domain name alone. Use the scan data below to understand what this site actually is.

Website: {domain}
Detected type: {site_label}
AI Readiness Score: {report.get('total_score', 0)}/100
Focus area: {focus}{insights_context}

Scan check results:
{checks_text}

Current content signals:
- Title: {current_title or 'Not detected from scan data'}
- Meta description: {current_meta_desc or 'Not detected from scan data'}
- H1 heading: {current_h1 or 'Not detected from scan data'}

Based on the ACTUAL scan data above, suggest optimized content that will make AI agents better understand and recommend this site.

Respond in this exact JSON format:
{{
  "suggestions": [
    {{
      "element": "Page Title",
      "current": "the actual current title from scan data, or your best inference from the domain and scan results",
      "suggested": "optimized title that AI agents will better parse and cite",
      "reason": "specific reason why this improves AI discoverability"
    }},
    {{
      "element": "Meta Description",
      "current": "actual or inferred meta description",
      "suggested": "optimized meta description (max 160 chars) for AI agent consumption",
      "reason": "specific reason"
    }},
    {{
      "element": "Main Heading (H1)",
      "current": "actual or inferred H1",
      "suggested": "optimized H1 for AI readability",
      "reason": "specific reason"
    }},
    {{
      "element": "Key Introductory Paragraph",
      "current": "inferred topic/content of intro paragraph",
      "suggested": "a clear, structured paragraph that helps AI agents quickly understand what this site offers",
      "reason": "why this helps AI agents"
    }}
  ],
  "general_tips": [
    "Specific actionable tip for this {site_label.lower()}",
    "Another specific tip",
    "Third tip"
  ]
}}

CRITICAL: Your suggestions must match what {domain} ACTUALLY does based on the scan data. Do not invent a business type that doesn't match the detected site type of "{site_label}"."""

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
