import re
import json
from urllib.parse import urljoin, urlparse
from xml.etree import ElementTree

import httpx
from bs4 import BeautifulSoup

USER_AGENT = "AgentCheck-Scanner/1.0 (Readiness Check)"
TIMEOUT = 15.0

PRODUCT_URL_PATTERNS = [
    r"/product[s]?/",
    r"/shop/",
    r"/item[s]?/",
    r"/p/",
    r"/artikel/",
    r"/produkt[e]?/",
    r"/sku/",
    r"/catalog/",
    r"/kollektion/",
]

PRODUCT_INDICATORS = [
    "add to cart",
    "in den warenkorb",
    "buy now",
    "jetzt kaufen",
    "kaufen",
    "bestellen",
]

PRICE_PATTERN = re.compile(r"[\$\€\£]\s?\d+[\.,]?\d{0,2}|\d+[\.,]\d{2}\s?[\$\€\£]")


async def find_product_pages(
    client: httpx.AsyncClient, base_url: str, html: str, max_pages: int = 3
) -> list[str]:
    """Discover product pages from sitemap, homepage links, and internal pages."""
    product_urls: set[str] = set()
    parsed_base = urlparse(base_url)

    # Strategy 1: Parse sitemap.xml
    sitemap_urls = await _parse_sitemap(client, base_url)
    for url in sitemap_urls:
        if _is_product_url(url):
            product_urls.add(url)
        if len(product_urls) >= max_pages:
            break

    # Strategy 2: Parse homepage links
    if len(product_urls) < max_pages:
        soup = BeautifulSoup(html, "lxml")
        for link in soup.find_all("a", href=True):
            href = link["href"]
            full_url = urljoin(base_url, href)
            parsed = urlparse(full_url)

            # Only internal links
            if parsed.netloc and parsed.netloc != parsed_base.netloc:
                continue

            # Check URL pattern
            if _is_product_url(full_url):
                product_urls.add(full_url)
                if len(product_urls) >= max_pages:
                    break
                continue

            # Check link text for product indicators
            link_text = link.get_text(strip=True).lower()
            if any(ind in link_text for ind in PRODUCT_INDICATORS):
                product_urls.add(full_url)
                if len(product_urls) >= max_pages:
                    break
                continue

            # Check for price patterns nearby
            if PRICE_PATTERN.search(link_text):
                product_urls.add(full_url)
                if len(product_urls) >= max_pages:
                    break

    # Strategy 3: Check a few internal pages for Product schema
    if len(product_urls) < max_pages:
        soup = BeautifulSoup(html, "lxml")
        internal_links = []
        for link in soup.find_all("a", href=True):
            full_url = urljoin(base_url, link["href"])
            parsed = urlparse(full_url)
            if (not parsed.netloc or parsed.netloc == parsed_base.netloc) and full_url not in product_urls:
                internal_links.append(full_url)

        # Check up to 5 internal pages
        for url in internal_links[:5]:
            if len(product_urls) >= max_pages:
                break
            try:
                resp = await client.get(url, follow_redirects=True, timeout=10.0)
                if resp.status_code == 200 and _has_product_schema(resp.text):
                    product_urls.add(url)
            except (httpx.RequestError, httpx.HTTPStatusError):
                continue

    return list(product_urls)[:max_pages]


async def _parse_sitemap(
    client: httpx.AsyncClient, base_url: str
) -> list[str]:
    """Parse sitemap.xml for URLs."""
    urls = []
    sitemap_locations = [
        f"{base_url}/sitemap.xml",
        f"{base_url}/sitemap_index.xml",
    ]

    for sitemap_url in sitemap_locations:
        try:
            resp = await client.get(sitemap_url, follow_redirects=True, timeout=10.0)
            if resp.status_code != 200:
                continue

            root = ElementTree.fromstring(resp.content)
            ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}

            # Check for sitemap index
            sitemaps = root.findall(".//sm:sitemap/sm:loc", ns)
            if sitemaps:
                # Get first product-related sub-sitemap
                for sitemap in sitemaps[:3]:
                    loc = sitemap.text
                    if loc and any(
                        kw in loc.lower()
                        for kw in ["product", "produkt", "shop", "catalog"]
                    ):
                        try:
                            sub_resp = await client.get(
                                loc, follow_redirects=True, timeout=10.0
                            )
                            if sub_resp.status_code == 200:
                                sub_root = ElementTree.fromstring(sub_resp.content)
                                for url_elem in sub_root.findall(
                                    ".//sm:url/sm:loc", ns
                                )[:20]:
                                    if url_elem.text:
                                        urls.append(url_elem.text)
                        except (httpx.RequestError, ElementTree.ParseError):
                            continue

            # Direct URL entries
            for url_elem in root.findall(".//sm:url/sm:loc", ns)[:50]:
                if url_elem.text:
                    urls.append(url_elem.text)

            if urls:
                break
        except (httpx.RequestError, ElementTree.ParseError):
            continue

    return urls


def _is_product_url(url: str) -> bool:
    """Check if URL matches product URL patterns."""
    url_lower = url.lower()
    return any(re.search(pattern, url_lower) for pattern in PRODUCT_URL_PATTERNS)


def _has_product_schema(html: str) -> bool:
    """Check if HTML contains Product schema."""
    soup = BeautifulSoup(html, "lxml")
    for script in soup.find_all("script", {"type": "application/ld+json"}):
        try:
            data = json.loads(script.string or "")
            if isinstance(data, dict):
                if data.get("@type") == "Product":
                    return True
                if "@graph" in data:
                    for item in data["@graph"]:
                        if isinstance(item, dict) and item.get("@type") == "Product":
                            return True
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and item.get("@type") == "Product":
                        return True
        except (json.JSONDecodeError, TypeError):
            continue
    return False
