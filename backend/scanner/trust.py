import httpx
from bs4 import BeautifulSoup

from scanner.models import CheckResult, CheckStatus


def check_aggregate_rating(schemas: list[dict]) -> CheckResult:
    """Check for AggregateRating in structured data."""
    for schema in schemas:
        if "aggregateRating" in schema:
            rating = schema["aggregateRating"]
            if isinstance(rating, dict) and "ratingValue" in rating:
                return CheckResult(
                    name="Aggregate Rating",
                    category="Trust Signals",
                    status=CheckStatus.PASS,
                    score=5,
                    max_score=5,
                    message=f"AggregateRating found (rating: {rating.get('ratingValue')}).",
                )
        if schema.get("@type") == "AggregateRating" and "ratingValue" in schema:
            return CheckResult(
                name="Aggregate Rating",
                category="Trust Signals",
                status=CheckStatus.PASS,
                score=5,
                max_score=5,
                message=f"AggregateRating found (rating: {schema.get('ratingValue')}).",
            )

    return CheckResult(
        name="Aggregate Rating",
        category="Trust Signals",
        status=CheckStatus.FAIL,
        score=0,
        max_score=5,
        message="No AggregateRating found in structured data.",
        fix_suggestion="Add AggregateRating to your Product schema to show review data to AI agents.",
    )


async def check_security(
    client: httpx.AsyncClient, base_url: str
) -> CheckResult:
    """Check HTTPS and security headers (HSTS, CSP)."""
    is_https = base_url.startswith("https://")

    try:
        resp = await client.get(base_url, follow_redirects=True)
        headers = resp.headers

        has_hsts = "strict-transport-security" in headers
        has_csp = "content-security-policy" in headers

        if is_https and has_hsts and has_csp:
            return CheckResult(
                name="HTTPS + Security Headers",
                category="Trust Signals",
                status=CheckStatus.PASS,
                score=5,
                max_score=5,
                message="HTTPS active with HSTS and CSP headers.",
            )
        elif is_https and (has_hsts or has_csp):
            present = []
            missing = []
            if has_hsts:
                present.append("HSTS")
            else:
                missing.append("HSTS")
            if has_csp:
                present.append("CSP")
            else:
                missing.append("CSP")
            return CheckResult(
                name="HTTPS + Security Headers",
                category="Trust Signals",
                status=CheckStatus.WARN,
                score=3,
                max_score=5,
                message=f"HTTPS active with {', '.join(present)}. Missing: {', '.join(missing)}.",
                fix_suggestion=f"Add {', '.join(missing)} header(s) for better security posture.",
            )
        elif is_https:
            return CheckResult(
                name="HTTPS + Security Headers",
                category="Trust Signals",
                status=CheckStatus.WARN,
                score=2,
                max_score=5,
                message="HTTPS active but missing HSTS and CSP headers.",
                fix_suggestion="Add Strict-Transport-Security and Content-Security-Policy headers.",
            )
        else:
            return CheckResult(
                name="HTTPS + Security Headers",
                category="Trust Signals",
                status=CheckStatus.FAIL,
                score=0,
                max_score=5,
                message="Site is not using HTTPS.",
                fix_suggestion="Enable HTTPS. It is essential for trust and required by modern AI agents.",
            )
    except httpx.RequestError:
        score = 1 if is_https else 0
        return CheckResult(
            name="HTTPS + Security Headers",
            category="Trust Signals",
            status=CheckStatus.WARN if is_https else CheckStatus.FAIL,
            score=score,
            max_score=5,
            message="Could not check security headers." + (" HTTPS detected in URL." if is_https else ""),
        )


def check_contact_info(html: str, schemas: list[dict]) -> CheckResult:
    """Check for contact and organization information."""
    # Check schema for contact info
    has_schema_contact = False
    for schema in schemas:
        schema_type = schema.get("@type", "")
        if schema_type in ("Organization", "LocalBusiness"):
            has_schema_contact = True
            break
        if "contactPoint" in schema:
            has_schema_contact = True
            break

    # Check HTML for contact indicators
    contact_keywords = [
        "contact us",
        "kontakt",
        "impressum",
        "email",
        "phone",
        "telefon",
        "customer service",
        "kundenservice",
        "support@",
        "info@",
    ]

    html_lower = html.lower()
    found_keywords = [k for k in contact_keywords if k in html_lower]

    if has_schema_contact and found_keywords:
        return CheckResult(
            name="Contact / Organization Info",
            category="Trust Signals",
            status=CheckStatus.PASS,
            score=5,
            max_score=5,
            message="Contact info in structured data and on page.",
        )
    elif has_schema_contact:
        return CheckResult(
            name="Contact / Organization Info",
            category="Trust Signals",
            status=CheckStatus.PASS,
            score=4,
            max_score=5,
            message="Organization info found in structured data.",
        )
    elif len(found_keywords) >= 2:
        return CheckResult(
            name="Contact / Organization Info",
            category="Trust Signals",
            status=CheckStatus.WARN,
            score=3,
            max_score=5,
            message=f"Contact info on page ({', '.join(found_keywords[:3])}) but not in structured data.",
            fix_suggestion="Add Organization schema with contactPoint for machine-readable contact info.",
        )
    elif found_keywords:
        return CheckResult(
            name="Contact / Organization Info",
            category="Trust Signals",
            status=CheckStatus.WARN,
            score=2,
            max_score=5,
            message="Minimal contact information found.",
            fix_suggestion="Add comprehensive contact info and Organization schema.",
        )
    else:
        return CheckResult(
            name="Contact / Organization Info",
            category="Trust Signals",
            status=CheckStatus.FAIL,
            score=0,
            max_score=5,
            message="No contact or organization information found.",
            fix_suggestion="Add contact details and an Organization schema to build trust with AI agents.",
        )


async def run_trust_checks(
    client: httpx.AsyncClient,
    base_url: str,
    html: str,
    schemas: list[dict],
) -> list[CheckResult]:
    """Run all trust signal checks."""
    results = [
        check_aggregate_rating(schemas),
        await check_security(client, base_url),
        check_contact_info(html, schemas),
    ]
    return results
