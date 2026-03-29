"""Detect website type from HTML content and structured data."""

import re

SITE_TYPES = {
    "ecommerce": {
        "label": "E-Commerce",
        "schema_types": ["Product", "Offer", "ShoppingCenter"],
        "html_signals": [
            "add to cart", "in den warenkorb", "buy now", "checkout",
            "shopping cart", "warenkorb", "price", "€", "$",
        ],
    },
    "blog": {
        "label": "Blog / News",
        "schema_types": ["Article", "NewsArticle", "BlogPosting", "Blog"],
        "html_signals": [
            "blog", "article", "posted on", "author", "read more",
            "published", "kategorie",
        ],
    },
    "saas": {
        "label": "SaaS / Software",
        "schema_types": ["SoftwareApplication", "WebApplication"],
        "html_signals": [
            "sign up", "free trial", "pricing", "demo", "api",
            "dashboard", "features", "integrations",
        ],
    },
    "restaurant": {
        "label": "Restaurant / Food",
        "schema_types": ["Restaurant", "FoodEstablishment", "Menu", "MenuItem"],
        "html_signals": [
            "menu", "reservierung", "reservation", "speisekarte",
            "öffnungszeiten", "opening hours", "book a table",
        ],
    },
    "local_business": {
        "label": "Local Business",
        "schema_types": ["LocalBusiness", "Store", "AutoRepair", "HealthAndBeautyBusiness"],
        "html_signals": [
            "opening hours", "öffnungszeiten", "visit us", "our location",
            "directions", "standort",
        ],
    },
    "professional_service": {
        "label": "Professional Service",
        "schema_types": ["ProfessionalService", "LegalService", "Physician", "Dentist", "FinancialService"],
        "html_signals": [
            "consultation", "beratung", "appointment", "termin",
            "our services", "leistungen", "about us",
        ],
    },
    "portfolio": {
        "label": "Portfolio / Agency",
        "schema_types": ["CreativeWork", "WebSite"],
        "html_signals": [
            "portfolio", "our work", "case study", "projects",
            "clients", "referenzen", "agentur", "agency",
        ],
    },
    "generic": {
        "label": "Website",
        "schema_types": ["WebSite", "Organization", "WebPage"],
        "html_signals": [],
    },
}


def _get_schema_types(schemas: list[dict]) -> set[str]:
    """Extract all @type values from a list of schema objects."""
    types: set[str] = set()
    for s in schemas:
        t = s.get("@type", "")
        if isinstance(t, list):
            types.update(t)
        elif isinstance(t, str) and t:
            types.add(t)
    return types


def detect_site_type(html: str, schemas: list[dict]) -> dict:
    """
    Detect the website type from HTML content and structured data.

    Returns {"type": "ecommerce", "label": "E-Commerce", "confidence": 0.85}
    """
    html_lower = html.lower()
    schema_types = _get_schema_types(schemas)

    scores: dict[str, float] = {}

    for site_type, config in SITE_TYPES.items():
        if site_type == "generic":
            continue

        score = 0.0

        # Schema type matches (weighted heavily)
        for st in config["schema_types"]:
            if st in schema_types:
                score += 3.0

        # HTML signal matches
        for signal in config["html_signals"]:
            if signal.lower() in html_lower:
                score += 1.0

        scores[site_type] = score

    if not scores or max(scores.values()) == 0:
        return {"type": "generic", "label": "Website", "confidence": 0.5}

    best_type = max(scores, key=scores.get)
    best_score = scores[best_type]

    # Calculate confidence based on how many signals matched vs total possible
    config = SITE_TYPES[best_type]
    max_possible = len(config["schema_types"]) * 3.0 + len(config["html_signals"]) * 1.0
    confidence = min(best_score / max_possible, 1.0) if max_possible > 0 else 0.5

    # Require a minimum threshold to avoid false positives
    if best_score < 2.0:
        return {"type": "generic", "label": "Website", "confidence": 0.5}

    return {
        "type": best_type,
        "label": config["label"],
        "confidence": round(confidence, 2),
    }
