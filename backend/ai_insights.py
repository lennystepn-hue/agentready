import os
import json
import httpx
import logging

logger = logging.getLogger(__name__)
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")


SITE_TYPE_CONTEXT = {
    "ecommerce": {
        "role": "e-commerce and AI shopping expert",
        "competitor_hint": "competing online stores in the same product category",
        "business_hint": "what this store sells and its target market",
    },
    "blog": {
        "role": "content publishing and AI discoverability expert",
        "competitor_hint": "competing blogs, news sites, or content platforms in the same niche",
        "business_hint": "what topics this blog/publication covers and its audience",
    },
    "saas": {
        "role": "SaaS marketing and AI discoverability expert",
        "competitor_hint": "competing SaaS products or tools that serve the same use case",
        "business_hint": "what this software does and who its target users are",
    },
    "restaurant": {
        "role": "restaurant marketing and AI local search expert",
        "competitor_hint": "competing restaurants or food businesses in the same area or cuisine type",
        "business_hint": "the cuisine type, location, and dining experience",
    },
    "local_business": {
        "role": "local business marketing and AI visibility expert",
        "competitor_hint": "competing local businesses offering similar services in the same area",
        "business_hint": "what services this business provides and its service area",
    },
    "professional_service": {
        "role": "professional services marketing and AI discoverability expert",
        "competitor_hint": "competing firms or professionals in the same field and region",
        "business_hint": "what professional services are offered and the target clientele",
    },
    "portfolio": {
        "role": "agency/portfolio marketing and AI visibility expert",
        "competitor_hint": "competing agencies, studios, or freelancers in the same creative field",
        "business_hint": "what creative or professional services this agency offers",
    },
    "generic": {
        "role": "digital presence and AI readiness expert",
        "competitor_hint": "similar websites or businesses in the same space",
        "business_hint": "what this website does and who it serves",
    },
}


async def generate_scan_insights(domain: str, report: dict) -> dict:
    """
    Generate AI-powered insights for a completed scan.
    Site-type-aware: adjusts prompt based on detected site type.
    Uses gpt-4o-mini for cost efficiency.
    """
    if not OPENAI_API_KEY:
        return {"error": "OpenAI API key not configured"}

    score = report.get("total_score", 0)
    grade = report.get("grade", "?")
    site_type = report.get("site_type", "generic")
    site_label = report.get("site_label", "Website")
    categories = report.get("categories", {})
    checks = report.get("checks", [])

    ctx = SITE_TYPE_CONTEXT.get(site_type, SITE_TYPE_CONTEXT["generic"])

    failed_checks = [c for c in checks if c.get("status") == "fail"]
    warned_checks = [c for c in checks if c.get("status") == "warn"]
    passed_checks = [c for c in checks if c.get("status") == "pass"]

    cat_summary = ""
    for name, data in categories.items():
        cat_summary += f"- {name}: {data.get('score', 0)}/{data.get('max_score', 0)}\n"

    issues = [c.get("name", "") for c in failed_checks[:10]]
    warnings = [c.get("name", "") for c in warned_checks[:10]]
    strengths = [c.get("name", "") for c in passed_checks[:5]]

    prompt = f"""You are a {ctx['role']}. Analyze this AI readiness scan for {domain}.

Site type: {site_label}
Score: {score}/100 (Grade: {grade})

Category scores:
{cat_summary}

Passed checks: {', '.join(strengths) if strengths else 'None'}
Critical issues (failed): {', '.join(issues) if issues else 'None'}
Warnings: {', '.join(warnings) if warnings else 'None'}

Respond in this exact JSON format:
{{
  "competitors": ["competitor1.com", "competitor2.com", "competitor3.com", "competitor4.com", "competitor5.com"],
  "market_segment": "{ctx['business_hint']}",
  "priority_actions": [
    "Most impactful action to take first",
    "Second most impactful action",
    "Third action"
  ],
  "strengths": [
    "What this site does well for AI readiness"
  ],
  "visibility_summary": "2-3 sentence summary of this {site_label.lower()}'s AI visibility and what it means for their business. Be specific to the site type.",
  "estimated_improvement": "Estimated point gain from implementing the top 3 fixes"
}}

For competitors: identify real {ctx['competitor_hint']} for {domain}. Use well-known sites that actually exist.
For market_segment: describe {ctx['business_hint']}.
For priority_actions: be specific and actionable, reference the actual failed checks. Tailor advice to a {site_label.lower()}.
For strengths: highlight 1-2 things they're already doing well based on passed checks.
Keep everything concise."""

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
                    "max_tokens": 500,
                    "temperature": 0.3,
                    "response_format": {"type": "json_object"},
                },
            )
            if resp.status_code == 200:
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                return json.loads(content)
            else:
                logger.warning(f"OpenAI API error: {resp.status_code} {resp.text[:200]}")
                return {"error": f"AI service unavailable (HTTP {resp.status_code})"}
    except Exception as e:
        logger.warning(f"AI insights generation failed: {e}")
        return {"error": str(e)[:200]}
