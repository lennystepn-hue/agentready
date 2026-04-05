#!/usr/bin/env python3
"""Screenshot card.html to PNG using Playwright"""
from playwright.sync_api import sync_playwright
import os

HTML = "/root/agentready/card.html"
OUT_OG = "/root/agentready/frontend/public/og-image.png"
OUT_TW = "/root/agentready/frontend/public/twitter-card.png"

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1200, "height": 630}, device_scale_factor=1)
    page.goto(f"file://{HTML}")
    page.wait_for_load_state("networkidle")
    page.screenshot(path=OUT_OG, type="png")
    page.screenshot(path=OUT_TW, type="png")
    browser.close()

for f in [OUT_OG, OUT_TW]:
    size = os.path.getsize(f)
    print(f"{f}: {size:,} bytes")
print("Done")
