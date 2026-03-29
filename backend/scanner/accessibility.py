import time
import re
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from scanner.models import CheckResult, CheckStatus

USER_AGENT = "AgentCheck-Scanner/1.0 (Readiness Check)"
TIMEOUT = 10.0


async def check_ttfb(client: httpx.AsyncClient, base_url: str) -> CheckResult:
    """Check Time To First Byte."""
    try:
        start = time.monotonic()
        resp = await client.get(base_url, follow_redirects=True)
        ttfb_ms = (time.monotonic() - start) * 1000

        if ttfb_ms < 500:
            return CheckResult(
                name="Response Time (TTFB)",
                category="Agent Accessibility",
                status=CheckStatus.PASS,
                score=5,
                max_score=5,
                message=f"TTFB is {ttfb_ms:.0f}ms (excellent).",
            )
        elif ttfb_ms < 1500:
            return CheckResult(
                name="Response Time (TTFB)",
                category="Agent Accessibility",
                status=CheckStatus.WARN,
                score=3,
                max_score=5,
                message=f"TTFB is {ttfb_ms:.0f}ms (acceptable but could be faster).",
                fix_suggestion="Optimize server response time. Consider caching, CDN, or server-side rendering.",
            )
        else:
            return CheckResult(
                name="Response Time (TTFB)",
                category="Agent Accessibility",
                status=CheckStatus.FAIL,
                score=0,
                max_score=5,
                message=f"TTFB is {ttfb_ms:.0f}ms (too slow for AI agents).",
                fix_suggestion="Significantly improve server response time. AI agents need fast responses.",
            )
    except httpx.RequestError as e:
        return CheckResult(
            name="Response Time (TTFB)",
            category="Agent Accessibility",
            status=CheckStatus.FAIL,
            score=0,
            max_score=5,
            message=f"Could not measure TTFB: {str(e)[:100]}",
        )


def check_js_dependency(html: str) -> CheckResult:
    """Check if content is accessible without JavaScript (body text heuristic)."""
    soup = BeautifulSoup(html, "lxml")

    # Remove script and style tags
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    body = soup.find("body")
    if not body:
        return CheckResult(
            name="JavaScript Dependency",
            category="Agent Accessibility",
            status=CheckStatus.FAIL,
            score=0,
            max_score=5,
            message="No body element found in HTML.",
            fix_suggestion="Ensure your pages have proper HTML structure accessible without JavaScript.",
        )

    text = body.get_text(separator=" ", strip=True)
    word_count = len(text.split())

    # Check for SPA indicators
    spa_indicators = [
        'id="__next"',
        'id="app"',
        'id="root"',
        "ng-app",
        "data-reactroot",
    ]
    html_lower = html.lower()
    is_spa = any(ind.lower() in html_lower for ind in spa_indicators)

    if word_count > 100:
        return CheckResult(
            name="JavaScript Dependency",
            category="Agent Accessibility",
            status=CheckStatus.PASS,
            score=5,
            max_score=5,
            message=f"Page has {word_count} words of content accessible without JS.",
        )
    elif word_count > 30:
        return CheckResult(
            name="JavaScript Dependency",
            category="Agent Accessibility",
            status=CheckStatus.WARN,
            score=3,
            max_score=5,
            message=f"Page has limited content ({word_count} words) without JS.",
            fix_suggestion="Implement server-side rendering (SSR) so AI agents can read your content.",
        )
    else:
        msg = "Page appears to require JavaScript to render content."
        if is_spa:
            msg += " SPA framework detected."
        return CheckResult(
            name="JavaScript Dependency",
            category="Agent Accessibility",
            status=CheckStatus.FAIL,
            score=0,
            max_score=5,
            message=msg,
            fix_suggestion="Use SSR or pre-rendering. AI agents typically cannot execute JavaScript.",
        )


async def check_api_availability(
    client: httpx.AsyncClient, base_url: str
) -> CheckResult:
    """Check for API endpoints, feeds, or sitemap."""
    endpoints_found = []

    checks = [
        (f"{base_url}/api/", "REST API"),
        (f"{base_url}/feeds/", "Data feeds"),
        (f"{base_url}/sitemap.xml", "XML Sitemap"),
        (f"{base_url}/products.json", "Products JSON feed"),
    ]

    for url, label in checks:
        try:
            resp = await client.get(url, follow_redirects=True)
            if resp.status_code == 200:
                endpoints_found.append(label)
        except httpx.RequestError:
            continue

    if len(endpoints_found) >= 2:
        return CheckResult(
            name="API / Feed Availability",
            category="Agent Accessibility",
            status=CheckStatus.PASS,
            score=5,
            max_score=5,
            message=f"Found: {', '.join(endpoints_found)}.",
        )
    elif endpoints_found:
        return CheckResult(
            name="API / Feed Availability",
            category="Agent Accessibility",
            status=CheckStatus.WARN,
            score=3,
            max_score=5,
            message=f"Found: {', '.join(endpoints_found)}. Consider adding more data access points.",
            fix_suggestion="Add a sitemap.xml and/or a product data feed for better agent access.",
        )
    else:
        return CheckResult(
            name="API / Feed Availability",
            category="Agent Accessibility",
            status=CheckStatus.FAIL,
            score=0,
            max_score=5,
            message="No API endpoints, feeds, or sitemap found.",
            fix_suggestion="Create a sitemap.xml and consider exposing a product API or JSON feed.",
        )


def check_url_structure(base_url: str, html: str) -> CheckResult:
    """Check if URLs are clean and human/agent-readable."""
    soup = BeautifulSoup(html, "lxml")
    links = soup.find_all("a", href=True)

    parsed_base = urlparse(base_url)
    internal_urls = []
    for link in links:
        href = link["href"]
        parsed = urlparse(href)
        if not parsed.netloc or parsed.netloc == parsed_base.netloc:
            internal_urls.append(href)

    if not internal_urls:
        return CheckResult(
            name="Clean URL Structure",
            category="Agent Accessibility",
            status=CheckStatus.WARN,
            score=2,
            max_score=5,
            message="Could not find internal links to evaluate URL structure.",
        )

    # Heuristics for bad URLs
    bad_patterns = 0
    sample_size = min(len(internal_urls), 50)
    checked = internal_urls[:sample_size]

    for url in checked:
        # Check for query-heavy, hash-fragment, or ID-based URLs
        if url.count("?") > 0 and url.count("&") >= 2:
            bad_patterns += 1
        elif re.search(r"/[a-f0-9]{24,}|/\d{8,}", url):
            bad_patterns += 1
        elif "#!" in url or "/#/" in url:
            bad_patterns += 1

    bad_ratio = bad_patterns / sample_size if sample_size > 0 else 0

    if bad_ratio < 0.1:
        return CheckResult(
            name="Clean URL Structure",
            category="Agent Accessibility",
            status=CheckStatus.PASS,
            score=5,
            max_score=5,
            message="URLs are clean and agent-readable.",
        )
    elif bad_ratio < 0.3:
        return CheckResult(
            name="Clean URL Structure",
            category="Agent Accessibility",
            status=CheckStatus.WARN,
            score=3,
            max_score=5,
            message=f"{bad_patterns}/{sample_size} URLs have complex patterns.",
            fix_suggestion="Use semantic, human-readable URLs (e.g., /products/blue-shirt instead of /p?id=12345).",
        )
    else:
        return CheckResult(
            name="Clean URL Structure",
            category="Agent Accessibility",
            status=CheckStatus.FAIL,
            score=0,
            max_score=5,
            message=f"{bad_patterns}/{sample_size} URLs are complex or opaque.",
            fix_suggestion="Restructure URLs to be clean and descriptive for both humans and AI agents.",
        )


async def run_accessibility_checks(
    client: httpx.AsyncClient, base_url: str, html: str
) -> list[CheckResult]:
    """Run all agent accessibility checks."""
    results = []
    results.append(await check_ttfb(client, base_url))
    results.append(check_js_dependency(html))
    results.append(await check_api_availability(client, base_url))
    results.append(check_url_structure(base_url, html))
    return results
