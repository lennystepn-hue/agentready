import json
import re

from bs4 import BeautifulSoup

from scanner.models import CheckResult, CheckStatus
from snippets.schema import (
    PRODUCT_SCHEMA_SNIPPET,
    ORGANIZATION_SCHEMA_SNIPPET,
    BREADCRUMB_SCHEMA_SNIPPET,
    ARTICLE_SCHEMA_SNIPPET,
    RESTAURANT_SCHEMA_SNIPPET,
    LOCAL_BUSINESS_SCHEMA_SNIPPET,
    SOFTWARE_APP_SCHEMA_SNIPPET,
    SERVICE_SCHEMA_SNIPPET,
)


def extract_jsonld(html: str) -> list[dict]:
    """Extract all JSON-LD blocks from HTML."""
    soup = BeautifulSoup(html, "lxml")
    schemas = []
    for script in soup.find_all("script", {"type": "application/ld+json"}):
        try:
            data = json.loads(script.string or "")
            if isinstance(data, list):
                schemas.extend(data)
            else:
                schemas.append(data)
        except (json.JSONDecodeError, TypeError):
            continue
    return schemas


def _flatten_graph(schemas: list[dict]) -> list[dict]:
    """Flatten @graph arrays into individual items."""
    flat = []
    for s in schemas:
        if "@graph" in s and isinstance(s["@graph"], list):
            flat.extend(s["@graph"])
        else:
            flat.append(s)
    return flat


def _find_by_type(schemas: list[dict], target_type: str) -> dict | None:
    """Find a schema object by @type."""
    for s in schemas:
        schema_type = s.get("@type", "")
        if isinstance(schema_type, list):
            if target_type in schema_type:
                return s
        elif schema_type == target_type:
            return s
    return None


def check_jsonld_presence(schemas: list[dict]) -> CheckResult:
    """Check if any JSON-LD structured data exists."""
    if schemas:
        return CheckResult(
            name="JSON-LD Structured Data",
            category="Structured Data Quality",
            status=CheckStatus.PASS,
            score=5,
            max_score=5,
            message=f"Found {len(schemas)} JSON-LD block(s).",
        )
    return CheckResult(
        name="JSON-LD Structured Data",
        category="Structured Data Quality",
        status=CheckStatus.FAIL,
        score=0,
        max_score=5,
        message="No JSON-LD structured data found.",
        fix_suggestion="Add JSON-LD structured data to your pages for better AI agent understanding.",
        code_snippet=ORGANIZATION_SCHEMA_SNIPPET,
    )


def check_product_schema(schemas: list[dict]) -> CheckResult:
    """Check Product schema with required fields."""
    product = _find_by_type(schemas, "Product")
    if not product:
        return CheckResult(
            name="Product Schema",
            category="Structured Data Quality",
            status=CheckStatus.FAIL,
            score=0,
            max_score=6,
            message="No Product schema found.",
            fix_suggestion="Add Product schema with name, description, image, sku, brand, and offers.",
            code_snippet=PRODUCT_SCHEMA_SNIPPET,
        )

    required = ["name", "description", "image", "sku", "brand", "offers"]
    found = [f for f in required if f in product]
    missing = [f for f in required if f not in product]
    ratio = len(found) / len(required)
    score = round(6 * ratio)

    if ratio == 1.0:
        return CheckResult(
            name="Product Schema",
            category="Structured Data Quality",
            status=CheckStatus.PASS,
            score=6,
            max_score=6,
            message="Product schema has all required fields.",
        )
    else:
        return CheckResult(
            name="Product Schema",
            category="Structured Data Quality",
            status=CheckStatus.WARN if ratio >= 0.5 else CheckStatus.FAIL,
            score=score,
            max_score=6,
            message=f"Product schema missing: {', '.join(missing)}.",
            fix_suggestion=f"Add the following fields to your Product schema: {', '.join(missing)}.",
            code_snippet=PRODUCT_SCHEMA_SNIPPET,
        )


def check_offer_schema(schemas: list[dict]) -> CheckResult:
    """Check Offer schema with required fields."""
    product = _find_by_type(schemas, "Product")
    offer = _find_by_type(schemas, "Offer")

    if product and "offers" in product:
        offers_data = product["offers"]
        if isinstance(offers_data, dict):
            offer = offers_data
        elif isinstance(offers_data, list) and offers_data:
            offer = offers_data[0]

    if not offer:
        return CheckResult(
            name="Offer Schema",
            category="Structured Data Quality",
            status=CheckStatus.FAIL,
            score=0,
            max_score=6,
            message="No Offer schema found.",
            fix_suggestion="Add Offer schema with price, priceCurrency, availability, and url.",
            code_snippet=PRODUCT_SCHEMA_SNIPPET,
        )

    required = ["price", "priceCurrency", "availability", "url"]
    found = [f for f in required if f in offer]
    missing = [f for f in required if f not in offer]
    ratio = len(found) / len(required)
    score = round(6 * ratio)

    if ratio == 1.0:
        return CheckResult(
            name="Offer Schema",
            category="Structured Data Quality",
            status=CheckStatus.PASS,
            score=6,
            max_score=6,
            message="Offer schema has all required fields.",
        )
    else:
        return CheckResult(
            name="Offer Schema",
            category="Structured Data Quality",
            status=CheckStatus.WARN if ratio >= 0.5 else CheckStatus.FAIL,
            score=score,
            max_score=6,
            message=f"Offer schema missing: {', '.join(missing)}.",
            fix_suggestion=f"Add these fields to your Offer schema: {', '.join(missing)}.",
        )


def check_organization_schema(schemas: list[dict]) -> CheckResult:
    """Check for Organization or LocalBusiness schema."""
    org = _find_by_type(schemas, "Organization") or _find_by_type(
        schemas, "LocalBusiness"
    )
    if org:
        has_name = "name" in org
        has_contact = "contactPoint" in org or "telephone" in org or "email" in org
        if has_name and has_contact:
            return CheckResult(
                name="Organization Schema",
                category="Structured Data Quality",
                status=CheckStatus.PASS,
                score=4,
                max_score=4,
                message="Organization/LocalBusiness schema found with contact info.",
            )
        elif has_name:
            return CheckResult(
                name="Organization Schema",
                category="Structured Data Quality",
                status=CheckStatus.WARN,
                score=2,
                max_score=4,
                message="Organization schema found but missing contact information.",
                fix_suggestion="Add contactPoint to your Organization schema.",
                code_snippet=ORGANIZATION_SCHEMA_SNIPPET,
            )
    return CheckResult(
        name="Organization Schema",
        category="Structured Data Quality",
        status=CheckStatus.FAIL,
        score=0,
        max_score=4,
        message="No Organization or LocalBusiness schema found.",
        fix_suggestion="Add an Organization schema with name, url, logo, and contactPoint.",
        code_snippet=ORGANIZATION_SCHEMA_SNIPPET,
    )


def check_article_schema(schemas: list[dict]) -> CheckResult:
    """Check for Article/BlogPosting/NewsArticle schema."""
    article = (
        _find_by_type(schemas, "Article")
        or _find_by_type(schemas, "BlogPosting")
        or _find_by_type(schemas, "NewsArticle")
    )
    if not article:
        return CheckResult(
            name="Article Schema",
            category="Structured Data Quality",
            status=CheckStatus.FAIL,
            score=0,
            max_score=6,
            message="No Article/BlogPosting schema found.",
            fix_suggestion="Add Article or BlogPosting schema with headline, author, datePublished, and image.",
            code_snippet=ARTICLE_SCHEMA_SNIPPET,
        )

    required = ["headline", "author", "datePublished", "image", "description"]
    found = [f for f in required if f in article]
    missing = [f for f in required if f not in article]
    ratio = len(found) / len(required)
    score = round(6 * ratio)

    if ratio == 1.0:
        return CheckResult(
            name="Article Schema",
            category="Structured Data Quality",
            status=CheckStatus.PASS,
            score=6,
            max_score=6,
            message="Article schema has all required fields.",
        )
    return CheckResult(
        name="Article Schema",
        category="Structured Data Quality",
        status=CheckStatus.WARN if ratio >= 0.5 else CheckStatus.FAIL,
        score=score,
        max_score=6,
        message=f"Article schema missing: {', '.join(missing)}.",
        fix_suggestion=f"Add the following fields to your Article schema: {', '.join(missing)}.",
        code_snippet=ARTICLE_SCHEMA_SNIPPET,
    )


def check_restaurant_schema(schemas: list[dict]) -> CheckResult:
    """Check for Restaurant/FoodEstablishment schema."""
    restaurant = (
        _find_by_type(schemas, "Restaurant")
        or _find_by_type(schemas, "FoodEstablishment")
    )
    if not restaurant:
        return CheckResult(
            name="Restaurant Schema",
            category="Structured Data Quality",
            status=CheckStatus.FAIL,
            score=0,
            max_score=6,
            message="No Restaurant schema found.",
            fix_suggestion="Add Restaurant schema with name, address, openingHoursSpecification, and servesCuisine.",
            code_snippet=RESTAURANT_SCHEMA_SNIPPET,
        )

    required = ["name", "address", "openingHoursSpecification", "servesCuisine", "telephone"]
    found = [f for f in required if f in restaurant]
    missing = [f for f in required if f not in restaurant]
    ratio = len(found) / len(required)
    score = round(6 * ratio)

    if ratio == 1.0:
        return CheckResult(
            name="Restaurant Schema",
            category="Structured Data Quality",
            status=CheckStatus.PASS,
            score=6,
            max_score=6,
            message="Restaurant schema has all required fields.",
        )
    return CheckResult(
        name="Restaurant Schema",
        category="Structured Data Quality",
        status=CheckStatus.WARN if ratio >= 0.5 else CheckStatus.FAIL,
        score=score,
        max_score=6,
        message=f"Restaurant schema missing: {', '.join(missing)}.",
        fix_suggestion=f"Add these fields to your Restaurant schema: {', '.join(missing)}.",
        code_snippet=RESTAURANT_SCHEMA_SNIPPET,
    )


def check_software_app_schema(schemas: list[dict]) -> CheckResult:
    """Check for SoftwareApplication/WebApplication schema."""
    app = (
        _find_by_type(schemas, "SoftwareApplication")
        or _find_by_type(schemas, "WebApplication")
    )
    if not app:
        return CheckResult(
            name="Software Application Schema",
            category="Structured Data Quality",
            status=CheckStatus.FAIL,
            score=0,
            max_score=6,
            message="No SoftwareApplication schema found.",
            fix_suggestion="Add SoftwareApplication schema with name, description, applicationCategory, and offers.",
            code_snippet=SOFTWARE_APP_SCHEMA_SNIPPET,
        )

    required = ["name", "description", "applicationCategory", "offers", "operatingSystem"]
    found = [f for f in required if f in app]
    missing = [f for f in required if f not in app]
    ratio = len(found) / len(required)
    score = round(6 * ratio)

    if ratio == 1.0:
        return CheckResult(
            name="Software Application Schema",
            category="Structured Data Quality",
            status=CheckStatus.PASS,
            score=6,
            max_score=6,
            message="SoftwareApplication schema has all required fields.",
        )
    return CheckResult(
        name="Software Application Schema",
        category="Structured Data Quality",
        status=CheckStatus.WARN if ratio >= 0.5 else CheckStatus.FAIL,
        score=score,
        max_score=6,
        message=f"SoftwareApplication schema missing: {', '.join(missing)}.",
        fix_suggestion=f"Add these fields to your SoftwareApplication schema: {', '.join(missing)}.",
        code_snippet=SOFTWARE_APP_SCHEMA_SNIPPET,
    )


def check_local_business_schema(schemas: list[dict]) -> CheckResult:
    """Check for LocalBusiness schema with address and hours."""
    biz = _find_by_type(schemas, "LocalBusiness")
    if not biz:
        # Check subtypes
        for subtype in ["Store", "AutoRepair", "HealthAndBeautyBusiness"]:
            biz = _find_by_type(schemas, subtype)
            if biz:
                break

    if not biz:
        return CheckResult(
            name="Local Business Schema",
            category="Structured Data Quality",
            status=CheckStatus.FAIL,
            score=0,
            max_score=6,
            message="No LocalBusiness schema found.",
            fix_suggestion="Add LocalBusiness schema with name, address, openingHoursSpecification, and telephone.",
            code_snippet=LOCAL_BUSINESS_SCHEMA_SNIPPET,
        )

    required = ["name", "address", "openingHoursSpecification", "telephone", "geo"]
    found = [f for f in required if f in biz]
    missing = [f for f in required if f not in biz]
    ratio = len(found) / len(required)
    score = round(6 * ratio)

    if ratio == 1.0:
        return CheckResult(
            name="Local Business Schema",
            category="Structured Data Quality",
            status=CheckStatus.PASS,
            score=6,
            max_score=6,
            message="LocalBusiness schema has all required fields.",
        )
    return CheckResult(
        name="Local Business Schema",
        category="Structured Data Quality",
        status=CheckStatus.WARN if ratio >= 0.5 else CheckStatus.FAIL,
        score=score,
        max_score=6,
        message=f"LocalBusiness schema missing: {', '.join(missing)}.",
        fix_suggestion=f"Add these fields to your LocalBusiness schema: {', '.join(missing)}.",
        code_snippet=LOCAL_BUSINESS_SCHEMA_SNIPPET,
    )


def check_service_schema(schemas: list[dict]) -> CheckResult:
    """Check for ProfessionalService or related service schema."""
    svc = _find_by_type(schemas, "ProfessionalService")
    if not svc:
        for subtype in ["LegalService", "Physician", "Dentist", "FinancialService"]:
            svc = _find_by_type(schemas, subtype)
            if svc:
                break

    if not svc:
        return CheckResult(
            name="Professional Service Schema",
            category="Structured Data Quality",
            status=CheckStatus.FAIL,
            score=0,
            max_score=6,
            message="No ProfessionalService schema found.",
            fix_suggestion="Add ProfessionalService schema with name, description, contactPoint, and areaServed.",
            code_snippet=SERVICE_SCHEMA_SNIPPET,
        )

    required = ["name", "description", "contactPoint", "address", "areaServed"]
    found = [f for f in required if f in svc]
    missing = [f for f in required if f not in svc]
    ratio = len(found) / len(required)
    score = round(6 * ratio)

    if ratio == 1.0:
        return CheckResult(
            name="Professional Service Schema",
            category="Structured Data Quality",
            status=CheckStatus.PASS,
            score=6,
            max_score=6,
            message="ProfessionalService schema has all required fields.",
        )
    return CheckResult(
        name="Professional Service Schema",
        category="Structured Data Quality",
        status=CheckStatus.WARN if ratio >= 0.5 else CheckStatus.FAIL,
        score=score,
        max_score=6,
        message=f"ProfessionalService schema missing: {', '.join(missing)}.",
        fix_suggestion=f"Add these fields to your service schema: {', '.join(missing)}.",
        code_snippet=SERVICE_SCHEMA_SNIPPET,
    )


def check_faq_schema(schemas: list[dict]) -> CheckResult:
    """Check for FAQPage schema."""
    faq = _find_by_type(schemas, "FAQPage")
    if faq and "mainEntity" in faq:
        items = faq["mainEntity"]
        count = len(items) if isinstance(items, list) else 1
        return CheckResult(
            name="FAQ Schema",
            category="Structured Data Quality",
            status=CheckStatus.PASS,
            score=4,
            max_score=4,
            message=f"FAQPage schema found with {count} question(s).",
        )
    if faq:
        return CheckResult(
            name="FAQ Schema",
            category="Structured Data Quality",
            status=CheckStatus.WARN,
            score=2,
            max_score=4,
            message="FAQPage schema found but missing mainEntity questions.",
            fix_suggestion="Add mainEntity with Question items to your FAQPage schema.",
        )
    return CheckResult(
        name="FAQ Schema",
        category="Structured Data Quality",
        status=CheckStatus.FAIL,
        score=0,
        max_score=4,
        message="No FAQPage schema found.",
        fix_suggestion="Add FAQPage schema to help AI agents answer common questions about your business.",
    )


def check_breadcrumb_schema(schemas: list[dict]) -> CheckResult:
    """Check for BreadcrumbList schema."""
    bc = _find_by_type(schemas, "BreadcrumbList")
    if bc and "itemListElement" in bc:
        items = bc["itemListElement"]
        if isinstance(items, list) and len(items) >= 2:
            return CheckResult(
                name="Breadcrumb Schema",
                category="Structured Data Quality",
                status=CheckStatus.PASS,
                score=4,
                max_score=4,
                message=f"BreadcrumbList schema found with {len(items)} items.",
            )
        return CheckResult(
            name="Breadcrumb Schema",
            category="Structured Data Quality",
            status=CheckStatus.WARN,
            score=2,
            max_score=4,
            message="BreadcrumbList found but with insufficient items.",
            fix_suggestion="Ensure your breadcrumb has at least 2 levels.",
        )
    return CheckResult(
        name="Breadcrumb Schema",
        category="Structured Data Quality",
        status=CheckStatus.FAIL,
        score=0,
        max_score=4,
        message="No BreadcrumbList schema found.",
        fix_suggestion="Add BreadcrumbList schema to help AI agents navigate your site hierarchy.",
        code_snippet=BREADCRUMB_SCHEMA_SNIPPET,
    )


def run_schema_checks(html: str, site_type: str = "generic") -> list[CheckResult]:
    """Run structured data checks on HTML content, adjusted for site type."""
    raw_schemas = extract_jsonld(html)
    schemas = _flatten_graph(raw_schemas)

    # Universal checks for all site types
    results = [
        check_jsonld_presence(schemas),
        check_organization_schema(schemas),
        check_breadcrumb_schema(schemas),
    ]

    # Site-type-specific checks
    if site_type == "ecommerce":
        results.append(check_product_schema(schemas))
        results.append(check_offer_schema(schemas))
    elif site_type == "blog":
        results.append(check_article_schema(schemas))
    elif site_type == "saas":
        results.append(check_software_app_schema(schemas))
        results.append(check_faq_schema(schemas))
    elif site_type == "restaurant":
        results.append(check_restaurant_schema(schemas))
    elif site_type == "local_business":
        results.append(check_local_business_schema(schemas))
    elif site_type == "professional_service":
        results.append(check_service_schema(schemas))
    elif site_type == "portfolio":
        # Portfolio sites mainly need Organization + Breadcrumb (already included)
        pass
    else:
        # Generic fallback: check for Product schema as a best-effort
        results.append(check_product_schema(schemas))
        results.append(check_offer_schema(schemas))

    return results
