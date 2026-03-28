AI_TXT_SNIPPET = """\
# ai.txt - AI Agent Instructions for Your Shop
# Place this file at https://yourshop.com/ai.txt

# Welcome
User-agent: *
Welcome: true

# Shop Information
Shop-name: Your Shop Name
Shop-type: e-commerce
Primary-language: en
Currencies: EUR, USD

# Agent Capabilities
Allow-product-search: true
Allow-price-comparison: true
Allow-add-to-cart: true
Allow-checkout: true
Allow-order-tracking: true

# API Endpoints
Products-API: /api/products
Search-API: /api/search
Cart-API: /api/cart

# Data Feeds
Product-feed: /feeds/products.json
Sitemap: /sitemap.xml

# Policies
Return-policy: /policies/returns
Shipping-policy: /policies/shipping
Privacy-policy: /policies/privacy

# Contact
Support-email: support@yourshop.com
Support-url: /contact
"""

LLMS_TXT_SNIPPET = """\
# llms.txt - Information for Large Language Models
# Place at https://yourshop.com/llms.txt or /.well-known/llms.txt

# Your Shop Name

> A brief description of your shop and what you sell.

## About
Your shop description, history, and unique selling points.

## Products
Overview of product categories and popular items.

## Policies
- Free shipping on orders over 50 EUR
- 30-day return policy
- Secure payment via credit card, PayPal, Klarna

## API Access
Developers and AI agents can access our product catalog
via our REST API at /api/products.

## Contact
- Email: support@yourshop.com
- Phone: +49-123-456789
"""
