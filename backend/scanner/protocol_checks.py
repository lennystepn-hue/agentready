import httpx
import json

from scanner.models import CheckResult, CheckStatus
from snippets.ucp import UCP_BASIC_SNIPPET
from snippets.ai_txt import AI_TXT_SNIPPET, LLMS_TXT_SNIPPET

USER_AGENT = "AgentCheck-Scanner/1.0 (Readiness Check)"
TIMEOUT = 15.0

AI_BOTS = [
    "GPTBot",
    "ChatGPT-User",
    "ClaudeBot",
    "Anthropic",
    "Google-Extended",
    "PerplexityBot",
    "CCBot",
]


async def check_ucp(client: httpx.AsyncClient, base_url: str) -> CheckResult:
    """Check for UCP endpoint at /.well-known/ucp."""
    url = f"{base_url}/.well-known/ucp"
    try:
        resp = await client.head(url, follow_redirects=True)
        if resp.status_code == 405:
            resp = await client.get(url, follow_redirects=True)

        if resp.status_code == 200:
            get_resp = await client.get(url, follow_redirects=True)
            try:
                data = get_resp.json()
                has_capabilities = "capabilities" in data
                has_business = "business" in data
                if has_capabilities and has_business:
                    return CheckResult(
                        name="UCP Endpoint",
                        category="Protocol Readiness",
                        status=CheckStatus.PASS,
                        score=8,
                        max_score=8,
                        message="UCP endpoint found with valid capabilities and business fields.",
                    )
                elif has_capabilities or has_business:
                    missing = "business" if not has_business else "capabilities"
                    return CheckResult(
                        name="UCP Endpoint",
                        category="Protocol Readiness",
                        status=CheckStatus.WARN,
                        score=4,
                        max_score=8,
                        message=f"UCP endpoint found but missing '{missing}' field.",
                        fix_suggestion=f"Add the '{missing}' field to your UCP JSON.",
                        code_snippet=UCP_BASIC_SNIPPET,
                    )
                else:
                    return CheckResult(
                        name="UCP Endpoint",
                        category="Protocol Readiness",
                        status=CheckStatus.WARN,
                        score=2,
                        max_score=8,
                        message="UCP endpoint returns JSON but missing required fields.",
                        fix_suggestion="Add 'capabilities' and 'business' fields to your UCP endpoint.",
                        code_snippet=UCP_BASIC_SNIPPET,
                    )
            except (json.JSONDecodeError, Exception):
                return CheckResult(
                    name="UCP Endpoint",
                    category="Protocol Readiness",
                    status=CheckStatus.WARN,
                    score=1,
                    max_score=8,
                    message="UCP endpoint exists but does not return valid JSON.",
                    fix_suggestion="Ensure /.well-known/ucp returns valid JSON with 'capabilities' and 'business' fields.",
                    code_snippet=UCP_BASIC_SNIPPET,
                )
        else:
            return CheckResult(
                name="UCP Endpoint",
                category="Protocol Readiness",
                status=CheckStatus.FAIL,
                score=0,
                max_score=8,
                message=f"No UCP endpoint found (HTTP {resp.status_code}).",
                fix_suggestion="Create a /.well-known/ucp endpoint that returns JSON describing your shop's agent capabilities.",
                code_snippet=UCP_BASIC_SNIPPET,
            )
    except httpx.RequestError as e:
        return CheckResult(
            name="UCP Endpoint",
            category="Protocol Readiness",
            status=CheckStatus.FAIL,
            score=0,
            max_score=8,
            message=f"Could not reach UCP endpoint: {str(e)[:100]}",
            fix_suggestion="Create a /.well-known/ucp endpoint.",
            code_snippet=UCP_BASIC_SNIPPET,
        )


async def check_ai_txt(client: httpx.AsyncClient, base_url: str) -> CheckResult:
    """Check for ai.txt file."""
    url = f"{base_url}/ai.txt"
    try:
        resp = await client.get(url, follow_redirects=True)
        if resp.status_code == 200 and len(resp.text.strip()) > 20:
            return CheckResult(
                name="ai.txt",
                category="Protocol Readiness",
                status=CheckStatus.PASS,
                score=4,
                max_score=4,
                message="ai.txt found with meaningful content.",
            )
        elif resp.status_code == 200:
            return CheckResult(
                name="ai.txt",
                category="Protocol Readiness",
                status=CheckStatus.WARN,
                score=2,
                max_score=4,
                message="ai.txt exists but has minimal content.",
                fix_suggestion="Add detailed AI agent instructions to your ai.txt file.",
                code_snippet=AI_TXT_SNIPPET,
            )
        else:
            return CheckResult(
                name="ai.txt",
                category="Protocol Readiness",
                status=CheckStatus.FAIL,
                score=0,
                max_score=4,
                message="No ai.txt file found.",
                fix_suggestion="Create an ai.txt file at your domain root with instructions for AI agents.",
                code_snippet=AI_TXT_SNIPPET,
            )
    except httpx.RequestError:
        return CheckResult(
            name="ai.txt",
            category="Protocol Readiness",
            status=CheckStatus.FAIL,
            score=0,
            max_score=4,
            message="Could not check for ai.txt.",
            fix_suggestion="Create an ai.txt file at your domain root.",
            code_snippet=AI_TXT_SNIPPET,
        )


async def check_llms_txt(client: httpx.AsyncClient, base_url: str) -> CheckResult:
    """Check for llms.txt at root or .well-known."""
    urls = [f"{base_url}/llms.txt", f"{base_url}/.well-known/llms.txt"]
    for url in urls:
        try:
            resp = await client.get(url, follow_redirects=True)
            if resp.status_code == 200 and len(resp.text.strip()) > 20:
                return CheckResult(
                    name="llms.txt",
                    category="Protocol Readiness",
                    status=CheckStatus.PASS,
                    score=4,
                    max_score=4,
                    message=f"llms.txt found at {url.replace(base_url, '')}.",
                )
        except httpx.RequestError:
            continue

    return CheckResult(
        name="llms.txt",
        category="Protocol Readiness",
        status=CheckStatus.FAIL,
        score=0,
        max_score=4,
        message="No llms.txt file found.",
        fix_suggestion="Create a llms.txt file for LLMs to understand your shop.",
        code_snippet=LLMS_TXT_SNIPPET,
    )


async def check_robots_txt(client: httpx.AsyncClient, base_url: str) -> CheckResult:
    """Check robots.txt for AI bot policies."""
    url = f"{base_url}/robots.txt"
    try:
        resp = await client.get(url, follow_redirects=True)
        if resp.status_code != 200:
            return CheckResult(
                name="robots.txt AI Policies",
                category="Protocol Readiness",
                status=CheckStatus.FAIL,
                score=0,
                max_score=4,
                message="No robots.txt found.",
                fix_suggestion="Create a robots.txt with explicit rules for AI bots.",
            )

        content = resp.text.lower()
        has_ai_rules = False
        for bot in AI_BOTS:
            if bot.lower() in content:
                has_ai_rules = True
                break

        if has_ai_rules:
            return CheckResult(
                name="robots.txt AI Policies",
                category="Protocol Readiness",
                status=CheckStatus.PASS,
                score=4,
                max_score=4,
                message="robots.txt contains explicit AI bot rules.",
            )
        elif "user-agent" in content:
            return CheckResult(
                name="robots.txt AI Policies",
                category="Protocol Readiness",
                status=CheckStatus.WARN,
                score=2,
                max_score=4,
                message="robots.txt exists but has no explicit AI bot rules.",
                fix_suggestion="Add User-agent rules for AI bots (GPTBot, ClaudeBot, etc.) to clarify your AI crawling policy.",
            )
        else:
            return CheckResult(
                name="robots.txt AI Policies",
                category="Protocol Readiness",
                status=CheckStatus.WARN,
                score=1,
                max_score=4,
                message="robots.txt exists but appears empty or minimal.",
                fix_suggestion="Add meaningful rules including AI bot policies.",
            )
    except httpx.RequestError:
        return CheckResult(
            name="robots.txt AI Policies",
            category="Protocol Readiness",
            status=CheckStatus.FAIL,
            score=0,
            max_score=4,
            message="Could not retrieve robots.txt.",
        )


async def run_protocol_checks(
    client: httpx.AsyncClient, base_url: str
) -> list[CheckResult]:
    """Run all protocol readiness checks."""
    results = []
    results.append(await check_ucp(client, base_url))
    results.append(await check_ai_txt(client, base_url))
    results.append(await check_llms_txt(client, base_url))
    results.append(await check_robots_txt(client, base_url))
    return results
