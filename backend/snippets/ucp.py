UCP_BASIC_SNIPPET = """\
// .well-known/ucp - Unified Commerce Protocol endpoint
// Serve this JSON at https://yoursite.com/.well-known/ucp
{
  "version": "1.0",
  "capabilities": {
    "product_search": true,
    "add_to_cart": true,
    "checkout": true,
    "order_tracking": true,
    "returns": true
  },
  "business": {
    "name": "Your Shop Name",
    "type": "e-commerce",
    "currency": "EUR",
    "languages": ["en", "de"],
    "support_email": "support@yourshop.com"
  },
  "endpoints": {
    "products": "/api/products",
    "cart": "/api/cart",
    "checkout": "/api/checkout",
    "orders": "/api/orders"
  },
  "authentication": {
    "type": "api_key",
    "header": "X-API-Key"
  }
}
"""

UCP_MINIMAL_SNIPPET = """\
// Minimal UCP endpoint for getting started
{
  "version": "1.0",
  "capabilities": {
    "product_search": true,
    "add_to_cart": false,
    "checkout": false
  },
  "business": {
    "name": "Your Shop Name",
    "type": "e-commerce",
    "currency": "EUR"
  }
}
"""
