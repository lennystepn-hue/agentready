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
            category="Transaction Readiness",
            status=CheckStatus.PASS,
            score=5,
            max_score=5,
            message=f"Guest checkout indicators found: {', '.join(found[:3])}.",
        )
    elif add_to_cart:
        return CheckResult(
            name="Guest Checkout",
            category="Transaction Readiness",
            status=CheckStatus.WARN,
            score=3,
            max_score=5,
            message="Add-to-cart found but no explicit guest checkout option detected.",
            fix_suggestion="Clearly indicate guest checkout availability on your site.",
        )
    else:
        return CheckResult(
            name="Guest Checkout",
            category="Transaction Readiness",
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
            category="Transaction Readiness",
            status=CheckStatus.PASS,
            score=5,
            max_score=5,
            message=f"Payment methods in schema and page. Found: {', '.join(found[:4])}.",
        )
    elif found and len(found) >= 2:
        return CheckResult(
            name="Payment Methods",
            category="Transaction Readiness",
            status=CheckStatus.WARN,
            score=3,
            max_score=5,
            message=f"Payment methods on page ({', '.join(found[:4])}) but not in structured data.",
            fix_suggestion="Add paymentAccepted to your Organization schema for machine-readable payment info.",
        )
    elif found:
        return CheckResult(
            name="Payment Methods",
            category="Transaction Readiness",
            status=CheckStatus.WARN,
            score=2,
            max_score=5,
            message=f"Minimal payment info found: {', '.join(found)}.",
            fix_suggestion="List all accepted payment methods and add them to structured data.",
        )
    else:
        return CheckResult(
            name="Payment Methods",
            category="Transaction Readiness",
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
            category="Transaction Readiness",
            status=CheckStatus.PASS,
            score=5,
            max_score=5,
            message="Shipping details found in structured data.",
        )
    elif found and len(found) >= 2:
        return CheckResult(
            name="Shipping Information",
            category="Transaction Readiness",
            status=CheckStatus.WARN,
            score=3,
            max_score=5,
            message=f"Shipping info on page but not in structured data. Keywords: {', '.join(found[:3])}.",
            fix_suggestion="Add OfferShippingDetails to your Product schema for machine-readable shipping info.",
        )
    elif found:
        return CheckResult(
            name="Shipping Information",
            category="Transaction Readiness",
            status=CheckStatus.WARN,
            score=2,
            max_score=5,
            message="Minimal shipping information found.",
            fix_suggestion="Add detailed shipping info with OfferShippingDetails in structured data.",
        )
    else:
        return CheckResult(
            name="Shipping Information",
            category="Transaction Readiness",
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
            category="Transaction Readiness",
            status=CheckStatus.PASS,
            score=5,
            max_score=5,
            message="Return policy found in structured data.",
        )
    elif found and len(found) >= 2:
        return CheckResult(
            name="Return Policy",
            category="Transaction Readiness",
            status=CheckStatus.WARN,
            score=3,
            max_score=5,
            message=f"Return policy on page but not structured. Keywords: {', '.join(found[:3])}.",
            fix_suggestion="Add MerchantReturnPolicy to your Offer schema for machine-readable return info.",
        )
    elif found:
        return CheckResult(
            name="Return Policy",
            category="Transaction Readiness",
            status=CheckStatus.WARN,
            score=2,
            max_score=5,
            message="Minimal return policy information found.",
            fix_suggestion="Add detailed return policy with MerchantReturnPolicy in structured data.",
        )
    else:
        return CheckResult(
            name="Return Policy",
            category="Transaction Readiness",
            status=CheckStatus.FAIL,
            score=0,
            max_score=5,
            message="No return policy information found.",
            fix_suggestion="Add a return policy to your pages and include MerchantReturnPolicy in your Offer schema.",
        )


def run_transaction_checks(html: str, schemas: list[dict]) -> list[CheckResult]:
    """Run all transaction readiness checks."""
    return [
        check_guest_checkout(html, schemas),
        check_payment_methods(html, schemas),
        check_shipping_info(html, schemas),
        check_return_policy(html, schemas),
    ]
