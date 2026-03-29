import json
import re

from bs4 import BeautifulSoup

from scanner.models import CheckResult, CheckStatus


def _search_html(html: str, patterns: list[str]) -> list[str]:
    """Search HTML for patterns (case-insensitive)."""
    found = []
    html_lower = html.lower()
    for pattern in patterns:
        if pattern.lower() in html_lower:
            found.append(pattern)
    return found


def _search_schema(schemas: list[dict], key: str) -> bool:
    """Recursively search schemas for a key."""
    for s in schemas:
        if key in s:
            return True
        for v in s.values():
            if isinstance(v, dict) and key in v:
                return True
            if isinstance(v, list):
                for item in v:
                    if isinstance(item, dict) and key in item:
                        return True
    return False


def check_guest_checkout(html: str, schemas: list[dict]) -> CheckResult:
    """Check for guest checkout indicators."""
    indicators = [
        "guest checkout",
        "buy as guest",
        "continue as guest",
        "checkout without account",
        "als Gast bestellen",
        "ohne Registrierung",
        "Gastzugang",
        "no account required",
        "express checkout",
    ]

    found = _search_html(html, indicators)

    # Also check for cart/checkout forms without login requirement
    soup = BeautifulSoup(html, "lxml")
    add_to_cart = soup.find_all(
        ["button", "a", "input"],
        string=re.compile(
            r"(add to cart|in den warenkorb|buy now|jetzt kaufen)", re.I
        ),
    )

    if found:
        return CheckResult(
            name="Guest Checkout",
            category="Conversion Readiness",
            status=CheckStatus.PASS,
            score=5,
            max_score=5,
            message=f"Guest checkout indicators found: {', '.join(found[:3])}.",
        )
    elif add_to_cart:
        return CheckResult(
            name="Guest Checkout",
            category="Conversion Readiness",
            status=CheckStatus.WARN,
            score=3,
            max_score=5,
            message="Add-to-cart found but no explicit guest checkout option detected.",
            fix_suggestion="Clearly indicate guest checkout availability on your site.",
        )
    else:
        return CheckResult(
            name="Guest Checkout",
            category="Conversion Readiness",
            status=CheckStatus.FAIL,
            score=0,
            max_score=5,
            message="No guest checkout indicators found.",
            fix_suggestion="Offer guest checkout and clearly label it. AI agents need frictionless purchasing flows.",
        )


def check_payment_methods(html: str, schemas: list[dict]) -> CheckResult:
    """Check for structured payment method information."""
    payment_keywords = [
        "visa",
        "mastercard",
        "paypal",
        "klarna",
        "apple pay",
        "google pay",
        "amex",
        "credit card",
        "kreditkarte",
        "sofort",
        "giropay",
        "sepa",
        "stripe",
        "afterpay",
    ]

    found = _search_html(html, payment_keywords)
    has_schema = _search_schema(schemas, "paymentAccepted") or _search_schema(
        schemas, "acceptedPaymentMethod"
    )

    if has_schema and found:
        return CheckResult(
            name="Payment Methods",
            category="Conversion Readiness",
            status=CheckStatus.PASS,
            score=5,
            max_score=5,
            message=f"Payment methods in schema and page. Found: {', '.join(found[:4])}.",
        )
    elif found and len(found) >= 2:
        return CheckResult(
            name="Payment Methods",
            category="Conversion Readiness",
            status=CheckStatus.WARN,
            score=3,
            max_score=5,
            message=f"Payment methods on page ({', '.join(found[:4])}) but not in structured data.",
            fix_suggestion="Add paymentAccepted to your Organization schema for machine-readable payment info.",
        )
    elif found:
        return CheckResult(
            name="Payment Methods",
            category="Conversion Readiness",
            status=CheckStatus.WARN,
            score=2,
            max_score=5,
            message=f"Minimal payment info found: {', '.join(found)}.",
            fix_suggestion="List all accepted payment methods and add them to structured data.",
        )
    else:
        return CheckResult(
            name="Payment Methods",
            category="Conversion Readiness",
            status=CheckStatus.FAIL,
            score=0,
            max_score=5,
            message="No payment method information found.",
            fix_suggestion="Display accepted payment methods and include them in your Organization schema.",
        )


def check_shipping_info(html: str, schemas: list[dict]) -> CheckResult:
    """Check for structured shipping information."""
    shipping_keywords = [
        "shipping",
        "delivery",
        "versand",
        "lieferung",
        "free shipping",
        "kostenloser versand",
        "shipping policy",
        "versandkosten",
        "delivery time",
        "lieferzeit",
    ]

    found = _search_html(html, shipping_keywords)
    has_schema = _search_schema(schemas, "shippingDetails") or _search_schema(
        schemas, "OfferShippingDetails"
    )

    if has_schema:
        return CheckResult(
            name="Shipping Information",
            category="Conversion Readiness",
            status=CheckStatus.PASS,
            score=5,
            max_score=5,
            message="Shipping details found in structured data.",
        )
    elif found and len(found) >= 2:
        return CheckResult(
            name="Shipping Information",
            category="Conversion Readiness",
            status=CheckStatus.WARN,
            score=3,
            max_score=5,
            message=f"Shipping info on page but not in structured data. Keywords: {', '.join(found[:3])}.",
            fix_suggestion="Add OfferShippingDetails to your Product schema for machine-readable shipping info.",
        )
    elif found:
        return CheckResult(
            name="Shipping Information",
            category="Conversion Readiness",
            status=CheckStatus.WARN,
            score=2,
            max_score=5,
            message="Minimal shipping information found.",
            fix_suggestion="Add detailed shipping info with OfferShippingDetails in structured data.",
        )
    else:
        return CheckResult(
            name="Shipping Information",
            category="Conversion Readiness",
            status=CheckStatus.FAIL,
            score=0,
            max_score=5,
            message="No shipping information found.",
            fix_suggestion="Add shipping details to your pages and Product schema.",
        )


def check_return_policy(html: str, schemas: list[dict]) -> CheckResult:
    """Check for structured return policy information."""
    return_keywords = [
        "return policy",
        "returns",
        "refund",
        "rückgabe",
        "widerruf",
        "widerrufsrecht",
        "rücksendung",
        "money back",
        "geld zurück",
        "return within",
        "rückgaberecht",
        "14 days",
        "30 days",
        "14 Tage",
        "30 Tage",
    ]

    found = _search_html(html, return_keywords)
    has_schema = _search_schema(
        schemas, "hasMerchantReturnPolicy"
    ) or _search_schema(schemas, "MerchantReturnPolicy")

    if has_schema:
        return CheckResult(
            name="Return Policy",
            category="Conversion Readiness",
            status=CheckStatus.PASS,
            score=5,
            max_score=5,
            message="Return policy found in structured data.",
        )
    elif found and len(found) >= 2:
        return CheckResult(
            name="Return Policy",
            category="Conversion Readiness",
            status=CheckStatus.WARN,
            score=3,
            max_score=5,
            message=f"Return policy on page but not structured. Keywords: {', '.join(found[:3])}.",
            fix_suggestion="Add MerchantReturnPolicy to your Offer schema for machine-readable return info.",
        )
    elif found:
        return CheckResult(
            name="Return Policy",
            category="Conversion Readiness",
            status=CheckStatus.WARN,
            score=2,
            max_score=5,
            message="Minimal return policy information found.",
            fix_suggestion="Add detailed return policy with MerchantReturnPolicy in structured data.",
        )
    else:
        return CheckResult(
            name="Return Policy",
            category="Conversion Readiness",
            status=CheckStatus.FAIL,
            score=0,
            max_score=5,
            message="No return policy information found.",
            fix_suggestion="Add a return policy to your pages and include MerchantReturnPolicy in your Offer schema.",
        )


def check_newsletter_rss(html: str, schemas: list[dict]) -> CheckResult:
    """Check for newsletter signup and RSS feed (blog sites)."""
    newsletter_keywords = [
        "newsletter", "subscribe", "sign up for updates", "email updates",
        "abonnieren", "benachrichtigung", "mailing list",
    ]
    rss_keywords = [
        "rss", "feed", "atom", "/feed", "/rss",
    ]
    social_keywords = [
        "share on", "share this", "tweet", "teilen", "social share",
    ]

    found_newsletter = _search_html(html, newsletter_keywords)
    found_rss = _search_html(html, rss_keywords)
    found_social = _search_html(html, social_keywords)

    total_found = len(found_newsletter) + len(found_rss) + len(found_social)
    all_found = found_newsletter + found_rss + found_social

    if total_found >= 3:
        return CheckResult(
            name="Newsletter / RSS / Social",
            category="Conversion Readiness",
            status=CheckStatus.PASS,
            score=5,
            max_score=5,
            message=f"Content distribution signals found: {', '.join(all_found[:4])}.",
        )
    elif total_found >= 1:
        return CheckResult(
            name="Newsletter / RSS / Social",
            category="Conversion Readiness",
            status=CheckStatus.WARN,
            score=3,
            max_score=5,
            message=f"Some distribution signals found: {', '.join(all_found[:3])}.",
            fix_suggestion="Add newsletter signup, RSS feed, and social sharing buttons to improve content distribution.",
        )
    return CheckResult(
        name="Newsletter / RSS / Social",
        category="Conversion Readiness",
        status=CheckStatus.FAIL,
        score=0,
        max_score=5,
        message="No newsletter, RSS, or social sharing signals found.",
        fix_suggestion="Add newsletter signup, an RSS feed, and social sharing buttons so AI agents can recommend your content.",
    )


def check_cta_presence(html: str, schemas: list[dict]) -> CheckResult:
    """Check for clear call-to-action elements."""
    cta_keywords = [
        "sign up", "get started", "free trial", "book a demo", "contact us",
        "request a quote", "learn more", "start now", "try free", "schedule",
        "jetzt starten", "kostenlos testen", "anfrage", "kontakt",
    ]
    found = _search_html(html, cta_keywords)

    # Also look for CTA-like buttons
    soup = BeautifulSoup(html, "lxml")
    cta_buttons = soup.find_all(
        ["button", "a"],
        string=re.compile(
            r"(get started|sign up|free trial|book|contact|anfrage|starten|demo)", re.I
        ),
    )

    total = len(found) + len(cta_buttons)

    if total >= 3:
        return CheckResult(
            name="Call-to-Action",
            category="Conversion Readiness",
            status=CheckStatus.PASS,
            score=5,
            max_score=5,
            message=f"Clear CTAs found: {', '.join(found[:4])}.",
        )
    elif total >= 1:
        return CheckResult(
            name="Call-to-Action",
            category="Conversion Readiness",
            status=CheckStatus.WARN,
            score=3,
            max_score=5,
            message=f"Some CTAs found: {', '.join(found[:3])}.",
            fix_suggestion="Add more prominent call-to-action buttons to help AI agents understand conversion paths.",
        )
    return CheckResult(
        name="Call-to-Action",
        category="Conversion Readiness",
        status=CheckStatus.FAIL,
        score=0,
        max_score=5,
        message="No clear call-to-action elements found.",
        fix_suggestion="Add clear CTAs (e.g., 'Get Started', 'Contact Us', 'Book a Demo') so AI agents can guide users to convert.",
    )


def check_contact_form(html: str, schemas: list[dict]) -> CheckResult:
    """Check for contact form or booking system."""
    contact_keywords = [
        "contact form", "kontaktformular", "get in touch", "send message",
        "nachricht senden", "book appointment", "termin buchen",
        "schedule a call", "request callback",
    ]
    found = _search_html(html, contact_keywords)

    soup = BeautifulSoup(html, "lxml")
    forms = soup.find_all("form")
    has_forms = len(forms) > 0

    if found and has_forms:
        return CheckResult(
            name="Contact / Booking Form",
            category="Conversion Readiness",
            status=CheckStatus.PASS,
            score=5,
            max_score=5,
            message=f"Contact/booking signals found: {', '.join(found[:3])}.",
        )
    elif found or has_forms:
        return CheckResult(
            name="Contact / Booking Form",
            category="Conversion Readiness",
            status=CheckStatus.WARN,
            score=3,
            max_score=5,
            message="Contact form or booking partially detected.",
            fix_suggestion="Make contact/booking options clearly labeled and easy to find.",
        )
    return CheckResult(
        name="Contact / Booking Form",
        category="Conversion Readiness",
        status=CheckStatus.FAIL,
        score=0,
        max_score=5,
        message="No contact form or booking system detected.",
        fix_suggestion="Add a contact form or booking system so AI agents can help users reach you.",
    )


def check_reservation_system(html: str, schemas: list[dict]) -> CheckResult:
    """Check for reservation/booking system (restaurant sites)."""
    reservation_keywords = [
        "reservation", "reservierung", "book a table", "tisch reservieren",
        "online booking", "opentable", "resy", "yelp reservations",
        "reserve", "buchung",
    ]
    menu_keywords = [
        "menu", "speisekarte", "our dishes", "unsere gerichte",
        "food menu", "getränkekarte", "wine list",
    ]
    delivery_keywords = [
        "delivery", "lieferung", "order online", "online bestellen",
        "takeaway", "zum mitnehmen", "uber eats", "lieferando",
    ]

    found_res = _search_html(html, reservation_keywords)
    found_menu = _search_html(html, menu_keywords)
    found_delivery = _search_html(html, delivery_keywords)

    total = len(found_res) + len(found_menu) + len(found_delivery)
    all_found = found_res + found_menu + found_delivery

    if total >= 4:
        return CheckResult(
            name="Reservation / Menu / Delivery",
            category="Conversion Readiness",
            status=CheckStatus.PASS,
            score=5,
            max_score=5,
            message=f"Restaurant conversion signals found: {', '.join(all_found[:4])}.",
        )
    elif total >= 2:
        return CheckResult(
            name="Reservation / Menu / Delivery",
            category="Conversion Readiness",
            status=CheckStatus.WARN,
            score=3,
            max_score=5,
            message=f"Some restaurant signals found: {', '.join(all_found[:3])}.",
            fix_suggestion="Add online reservation, a visible menu, and delivery options for better AI agent integration.",
        )
    return CheckResult(
        name="Reservation / Menu / Delivery",
        category="Conversion Readiness",
        status=CheckStatus.FAIL,
        score=0,
        max_score=5,
        message="No reservation, menu, or delivery signals found.",
        fix_suggestion="Add online reservation, menu page, and delivery options. AI agents need these to recommend your restaurant.",
    )


def check_pricing_page(html: str, schemas: list[dict]) -> CheckResult:
    """Check for pricing page and trial/demo options (SaaS sites)."""
    pricing_keywords = [
        "pricing", "plans", "preise", "free trial", "start free",
        "request demo", "api docs", "api documentation", "developer",
        "documentation", "free plan", "enterprise",
    ]
    found = _search_html(html, pricing_keywords)

    if len(found) >= 3:
        return CheckResult(
            name="Pricing / Trial / API Docs",
            category="Conversion Readiness",
            status=CheckStatus.PASS,
            score=5,
            max_score=5,
            message=f"SaaS conversion signals found: {', '.join(found[:4])}.",
        )
    elif len(found) >= 1:
        return CheckResult(
            name="Pricing / Trial / API Docs",
            category="Conversion Readiness",
            status=CheckStatus.WARN,
            score=3,
            max_score=5,
            message=f"Some SaaS signals found: {', '.join(found[:3])}.",
            fix_suggestion="Add clear pricing, free trial option, and API documentation links.",
        )
    return CheckResult(
        name="Pricing / Trial / API Docs",
        category="Conversion Readiness",
        status=CheckStatus.FAIL,
        score=0,
        max_score=5,
        message="No pricing, trial, or API documentation found.",
        fix_suggestion="Add a pricing page, free trial option, and API docs so AI agents can recommend your SaaS product.",
    )


def check_directions_map(html: str, schemas: list[dict]) -> CheckResult:
    """Check for directions/map (local business sites)."""
    map_keywords = [
        "directions", "wegbeschreibung", "how to find us", "anfahrt",
        "google maps", "our location", "unser standort",
        "visit us", "besuchen sie uns", "map",
    ]
    found = _search_html(html, map_keywords)

    # Check for embedded maps
    soup = BeautifulSoup(html, "lxml")
    iframes = soup.find_all("iframe")
    has_map = any("map" in (iframe.get("src", "") or "").lower() for iframe in iframes)

    if found and has_map:
        return CheckResult(
            name="Directions / Map",
            category="Conversion Readiness",
            status=CheckStatus.PASS,
            score=5,
            max_score=5,
            message=f"Location/directions signals found: {', '.join(found[:3])}.",
        )
    elif found or has_map:
        return CheckResult(
            name="Directions / Map",
            category="Conversion Readiness",
            status=CheckStatus.WARN,
            score=3,
            max_score=5,
            message="Partial location information found.",
            fix_suggestion="Add an embedded map and clear directions to help AI agents guide visitors to your location.",
        )
    return CheckResult(
        name="Directions / Map",
        category="Conversion Readiness",
        status=CheckStatus.FAIL,
        score=0,
        max_score=5,
        message="No directions or map information found.",
        fix_suggestion="Add an embedded map and directions to help AI agents guide visitors to your location.",
    )


def run_transaction_checks(html: str, schemas: list[dict], site_type: str = "generic") -> list[CheckResult]:
    """Run conversion readiness checks adjusted for the detected site type."""
    if site_type == "ecommerce":
        return [
            check_guest_checkout(html, schemas),
            check_payment_methods(html, schemas),
            check_shipping_info(html, schemas),
            check_return_policy(html, schemas),
        ]
    elif site_type == "blog":
        return [
            check_newsletter_rss(html, schemas),
            check_cta_presence(html, schemas),
            check_contact_form(html, schemas),
        ]
    elif site_type == "saas":
        return [
            check_pricing_page(html, schemas),
            check_cta_presence(html, schemas),
            check_contact_form(html, schemas),
        ]
    elif site_type == "restaurant":
        return [
            check_reservation_system(html, schemas),
            check_contact_form(html, schemas),
            check_directions_map(html, schemas),
        ]
    elif site_type == "local_business":
        return [
            check_contact_form(html, schemas),
            check_directions_map(html, schemas),
            check_cta_presence(html, schemas),
        ]
    elif site_type == "professional_service":
        return [
            check_contact_form(html, schemas),
            check_cta_presence(html, schemas),
            check_directions_map(html, schemas),
        ]
    elif site_type == "portfolio":
        return [
            check_cta_presence(html, schemas),
            check_contact_form(html, schemas),
        ]
    else:
        # Generic: check broad conversion signals
        return [
            check_cta_presence(html, schemas),
            check_contact_form(html, schemas),
        ]
