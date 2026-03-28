import json
import logging
from datetime import datetime, timezone

import httpx

from scanner.models import CheckResult, CheckStatus, ScanReport, calculate_grade
from scanner.protocol_checks import run_protocol_checks
from scanner.schema_checks import run_schema_checks, extract_jsonld, _flatten_graph
from scanner.accessibility import run_accessibility_checks
from scanner.transaction import run_transaction_checks
from scanner.trust import run_trust_checks
from scanner.discovery import find_product_pages
from db import update_scan_result

USER_AGENT = "AgentReady-Scanner/1.0 (Readiness Check)"
TIMEOUT = 20.0

logger = logging.getLogger(__name__)


async def run_scan(scan_id: str, domain: str) -> None:
    """Execute a full agent readiness scan for a domain."""
    base_url = f"https://{domain}"

    try:
        await update_scan_result(scan_id, status="running")

        async with httpx.AsyncClient(
            headers={"User-Agent": USER_AGENT},
            timeout=TIMEOUT,
            follow_redirects=True,
        ) as client:
            # Fetch homepage
            try:
                homepage_resp = await client.get(base_url)
                homepage_html = homepage_resp.text
            except httpx.RequestError:
                # Try HTTP fallback
                try:
                    base_url = f"http://{domain}"
                    homepage_resp = await client.get(base_url)
                    homepage_html = homepage_resp.text
                except httpx.RequestError as e:
                    await update_scan_result(
                        scan_id,
                        status="error",
                        report_json=json.dumps(
                            {"error": f"Could not reach {domain}: {str(e)[:200]}"}
                        ),
                    )
                    return

            all_checks: list[CheckResult] = []

            # 1. Protocol checks
            protocol_results = await run_protocol_checks(client, base_url)
            all_checks.extend(protocol_results)

            # 2. Extract structured data from homepage
            raw_schemas = extract_jsonld(homepage_html)
            schemas = _flatten_graph(raw_schemas)

            # 3. Schema checks on homepage
            schema_results = run_schema_checks(homepage_html)
            all_checks.extend(schema_results)

            # 4. Discover product pages and analyze them
            product_pages = await find_product_pages(
                client, base_url, homepage_html, max_pages=3
            )

            # Merge schemas from product pages
            for page_url in product_pages:
                try:
                    resp = await client.get(page_url)
                    page_schemas = _flatten_graph(extract_jsonld(resp.text))
                    schemas.extend(page_schemas)

                    # If homepage had no Product schema, check product pages
                    page_schema_results = run_schema_checks(resp.text)
                    # Replace FAIL results with better results from product pages
                    for new_check in page_schema_results:
                        for i, existing in enumerate(all_checks):
                            if (
                                existing.name == new_check.name
                                and existing.category == new_check.category
                                and new_check.score > existing.score
                            ):
                                all_checks[i] = new_check
                                break
                except (httpx.RequestError, httpx.HTTPStatusError):
                    continue

            # Combine all HTML for content analysis
            combined_html = homepage_html
            for page_url in product_pages[:2]:
                try:
                    resp = await client.get(page_url)
                    combined_html += "\n" + resp.text
                except (httpx.RequestError, httpx.HTTPStatusError):
                    continue

            # 5. Accessibility checks
            accessibility_results = await run_accessibility_checks(
                client, base_url, homepage_html
            )
            all_checks.extend(accessibility_results)

            # 6. Transaction checks
            transaction_results = run_transaction_checks(combined_html, schemas)
            all_checks.extend(transaction_results)

            # 7. Trust checks
            trust_results = await run_trust_checks(
                client, base_url, combined_html, schemas
            )
            all_checks.extend(trust_results)

            # Calculate scores
            total_score = sum(c.score for c in all_checks)
            max_score = sum(c.max_score for c in all_checks)

            # Normalize to 100
            normalized_score = round((total_score / max_score) * 100) if max_score > 0 else 0
            grade = calculate_grade(normalized_score)

            # Category breakdown
            categories = {}
            for check in all_checks:
                cat = check.category
                if cat not in categories:
                    categories[cat] = {"score": 0, "max_score": 0, "checks": 0}
                categories[cat]["score"] += check.score
                categories[cat]["max_score"] += check.max_score
                categories[cat]["checks"] += 1

            # Top fixes: failed/warned checks sorted by potential score gain
            top_fixes = sorted(
                [c for c in all_checks if c.status != CheckStatus.PASS],
                key=lambda c: c.max_score - c.score,
                reverse=True,
            )[:5]

            report = ScanReport(
                domain=domain,
                scan_id=scan_id,
                timestamp=datetime.now(timezone.utc).isoformat(),
                total_score=normalized_score,
                max_score=100,
                grade=grade,
                categories=categories,
                checks=all_checks,
                top_fixes=top_fixes,
            )

            await update_scan_result(
                scan_id,
                status="completed",
                total_score=normalized_score,
                grade=grade,
                report_json=json.dumps(report.to_dict()),
            )

    except Exception as e:
        logger.exception(f"Scan {scan_id} failed with unexpected error")
        await update_scan_result(
            scan_id,
            status="error",
            report_json=json.dumps({"error": f"Scan failed: {str(e)[:300]}"}),
        )
