import os
import json
import httpx
import logging

logger = logging.getLogger(__name__)
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")


async def generate_scan_insights(domain: str, report: dict) -> dict:
    """
    Generate AI-powered insights for a completed scan.
    Returns competitors, smart recommendations, and visibility summary.
    Uses gpt-4o-mini for cost efficiency.
    """
    if not OPENAI_API_KEY:
        return {"error": "OpenAI API key not configured"}

    # Build a concise summary of the scan for the prompt
    score = report.get("total_score", 0)
    grade = report.get("grade", "?")
    categories = report.get("categories", {})
    checks = report.get("checks", [])

    failed_checks = [c for c in checks if c.get("status") == "fail"]
    warned_checks = [c for c in checks if c.get("status") == "warn"]

    # Category scores summary
    cat_summary = ""
    for name, data in categories.items():
        cat_summary += f"- {name}: {data.get('score', 0)}/{data.get('max_score', 0)}\n"

    # Failed/warned check names
    issues = [c.get("name", "") for c in failed_checks[:10]]
    warnings = [c.get("name", "") for c in warned_checks[:10]]

    prompt = f"""You are an e-commerce AI readiness expert. Analyze this scan result for {domain}.

Score: {score}/100 (Grade: {grade})

Category scores:
{cat_summary}

Critical issues (failed checks): {', '.join(issues) if issues else 'None'}
Warnings: {', '.join(warnings) if warnings else 'None'}

Respond in this exact JSON format:
{{
  "competitors": ["competitor1.com", "competitor2.com", "competitor3.com", "competitor4.com", "competitor5.com"],
  "market_segment": "Brief description of what this store sells/does",
  "priority_actions": [
    "Most impactful action to take first",
    "Second most impactful action",
    "Third action"
  ],
  "visibility_summary": "2-3 sentence natural language summary of the store's AI visibility status and what it means for their business",
  "estimated_improvement": "How many points they could gain by implementing the top 3 fixes"
}}

For competitors: identify real competing e-commerce stores in the same market segment as {domain}. Use well-known stores that actually exist.
For priority_actions: be specific and actionable, reference the actual failed checks.
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
