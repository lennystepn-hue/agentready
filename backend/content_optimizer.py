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

    # Build check summaries for context
    check_summaries = []
    for check in checks[:8]:
        check_summaries.append(f"- {check.get('name', '?')}: {check.get('status', '?')} — {check.get('message', '')[:80]}")
    checks_text = "\n".join(check_summaries) if check_summaries else "No check data."

    # Actually fetch the homepage to get real content
    real_title = ""
    real_meta_desc = ""
    real_h1 = ""
    real_intro = ""
    try:
        from bs4 import BeautifulSoup
        async with httpx.AsyncClient(timeout=12, follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (compatible; AgentCheck/1.0)"}) as http_client:
            resp = await http_client.get(f"https://{domain}")
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "lxml")
                title_tag = soup.find("title")
                if title_tag and title_tag.string:
                    real_title = title_tag.string.strip()[:200]
                meta_desc_tag = soup.find("meta", attrs={"name": "description"})
                if meta_desc_tag:
                    real_meta_desc = (meta_desc_tag.get("content", "") or "")[:300]
                h1_tag = soup.find("h1")
                if h1_tag:
                    real_h1 = h1_tag.get_text(strip=True)[:200]
                # Get first meaningful paragraph
                for p in soup.find_all("p"):
                    text = p.get_text(strip=True)
                    if len(text) > 50:
                        real_intro = text[:300]
                        break
    except Exception as e:
        logger.warning(f"Could not fetch {domain} for content optimization: {e}")

    # Get AI insights if cached
    insights_context = ""
    scan_insights = scan.get("ai_insights_json", "")
    if scan_insights:
        try:
            ins = json.loads(scan_insights)
            if ins.get("market_segment"):
                insights_context = f"\nWhat this site does: {ins['market_segment']}"
            if ins.get("visibility_summary"):
                insights_context += f"\nAI visibility: {ins['visibility_summary'][:200]}"
            if ins.get("competitors"):
                insights_context += f"\nCompetitors: {', '.join(ins['competitors'][:3])}"
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

ACTUAL current content (fetched from live site):
- Title: {real_title or 'Could not detect'}
- Meta description: {real_meta_desc or 'Could not detect'}
- H1 heading: {real_h1 or 'Could not detect'}
- First paragraph: {real_intro or 'Could not detect'}

Based on the ACTUAL scan data above, suggest optimized content that will make AI agents better understand and recommend this site.

Respond in this exact JSON format:
{{
  "suggestions": [
    {{
      "element": "Page Title",
      "current": "{real_title or 'Not detected'}",
      "suggested": "optimized title that AI agents will better parse and cite — must accurately describe what {domain} actually does",
      "reason": "specific reason why this improves AI discoverability"
    }},
    {{
      "element": "Meta Description",
      "current": "{real_meta_desc or 'Not detected'}",
      "suggested": "optimized meta description (max 160 chars) — must accurately describe {domain}",
      "reason": "specific reason"
    }},
    {{
      "element": "Main Heading (H1)",
      "current": "{real_h1 or 'Not detected'}",
      "suggested": "optimized H1 that clearly states what {domain} does",
      "reason": "specific reason"
    }},
    {{
      "element": "Key Introductory Paragraph",
      "current": "{real_intro[:100] or 'Not detected'}",
      "suggested": "a clear paragraph that helps AI agents understand what {domain} offers — use the actual content above as basis",
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
