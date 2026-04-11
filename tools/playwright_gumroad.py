#!/usr/bin/env python3
"""
playwright_gumroad.py

Creates a Gumroad product via browser automation (Playwright).
Use this when the API token isn't working — no API key needed,
just your Gumroad email/password in the environment or .env file.

Setup (one-time):
    pip install playwright
    playwright install chromium

Usage:
    python tools/playwright_gumroad.py

Credentials (set ONE of these ways):
    $env:GUMROAD_EMAIL    = "you@example.com"
    $env:GUMROAD_PASSWORD = "yourpassword"
  OR add them to your .env file:
    GUMROAD_EMAIL=you@example.com
    GUMROAD_PASSWORD=yourpassword
"""

import os
import sys
import time

# ── load .env if present ────────────────────────────────────────────────────
def load_dotenv():
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    if not os.path.exists(env_path):
        return
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key not in os.environ:
                os.environ[key] = val

load_dotenv()

EMAIL    = os.environ.get("GUMROAD_EMAIL", "")
PASSWORD = os.environ.get("GUMROAD_PASSWORD", "")

if not EMAIL or not PASSWORD:
    print("ERROR: Set GUMROAD_EMAIL and GUMROAD_PASSWORD in your environment or .env file.")
    sys.exit(1)

# ── product definition ───────────────────────────────────────────────────────
PRODUCT_NAME  = "Developer Productivity Prompt Pack"
PRODUCT_PRICE = "9"
PRODUCT_DESC  = """30 sharp, battle-tested prompts for developers who use AI daily. Code review, debugging, architecture, communication, and workflow. No fluff. Just prompts that actually work.

Includes 5 sections:
- Code Review & Quality (6 prompts)
- Debugging & Problem Solving (6 prompts)
- Architecture & Design (6 prompts)
- Writing & Communication (6 prompts)
- Productivity & Workflow (6 prompts)

Built by Em for ForgeCore."""

CONTENT_FILE  = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "products", "developer-productivity-prompt-pack.md"
)

# ── browser automation ───────────────────────────────────────────────────────
def create_product():
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # headless=False so you can watch / intervene
        page = browser.new_page()

        print("[playwright] Navigating to Gumroad login...")
        page.goto("https://app.gumroad.com/login", wait_until="networkidle")

        # ── login ────────────────────────────────────────────────────────────
        print("[playwright] Logging in...")
        page.fill('input[name="email"]', EMAIL)
        page.fill('input[name="password"]', PASSWORD)
        page.click('button[type="submit"]')

        try:
            page.wait_for_url("**/dashboard**", timeout=15000)
            print("[playwright] Logged in successfully.")
        except PWTimeout:
            # May have landed on 2FA or different page — pause for human intervention
            print("[playwright] Login may need manual help (2FA?). Waiting 30s for you to complete it...")
            time.sleep(30)

        # ── navigate to new product ──────────────────────────────────────────
        print("[playwright] Opening new product page...")
        page.goto("https://app.gumroad.com/products/new", wait_until="networkidle")
        time.sleep(2)

        # ── fill product name ────────────────────────────────────────────────
        print("[playwright] Setting product name...")
        name_input = page.locator('input[placeholder*="name"], input[name="name"], input[id*="name"]').first
        name_input.click()
        name_input.fill(PRODUCT_NAME)

        # ── set price ────────────────────────────────────────────────────────
        print("[playwright] Setting price...")
        price_input = page.locator('input[placeholder*="price"], input[name="price"], input[id*="price"]').first
        price_input.click()
        price_input.fill(PRODUCT_PRICE)

        # ── save to get to full editor ───────────────────────────────────────
        print("[playwright] Saving initial product...")
        save_btn = page.locator('button:has-text("Save"), button:has-text("Next"), button[type="submit"]').first
        save_btn.click()
        time.sleep(3)

        # ── fill description in the editor ───────────────────────────────────
        print("[playwright] Adding description...")
        try:
            desc_area = page.locator('textarea[name="description"], div[contenteditable="true"], .ql-editor').first
            desc_area.click()
            desc_area.fill(PRODUCT_DESC)
        except Exception as e:
            print(f"[playwright] Description field not found automatically: {e}")
            print("[playwright] Please paste the description manually in the browser window.")
            time.sleep(20)

        # ── upload the content file ──────────────────────────────────────────
        if os.path.exists(CONTENT_FILE):
            print("[playwright] Uploading content file...")
            try:
                file_input = page.locator('input[type="file"]').first
                file_input.set_input_files(CONTENT_FILE)
                time.sleep(3)
                print("[playwright] File uploaded.")
            except Exception as e:
                print(f"[playwright] File upload not found automatically: {e}")
                print("[playwright] Please upload the file manually in the browser window.")
                time.sleep(20)
        else:
            print(f"[playwright] WARNING: Content file not found at {CONTENT_FILE}")

        # ── save / publish ───────────────────────────────────────────────────
        print("[playwright] Saving product...")
        try:
            save_btn = page.locator('button:has-text("Save"), button:has-text("Publish")').first
            save_btn.click()
            time.sleep(3)
        except Exception as e:
            print(f"[playwright] Save button issue: {e}")

        # ── grab the product URL ─────────────────────────────────────────────
        print("[playwright] Checking for product URL...")
        try:
            url_el = page.locator('a[href*="gumroad.com/l/"]').first
            product_url = url_el.get_attribute("href")
            print(f"[playwright] ✅ Product live at: {product_url}")
        except Exception:
            print("[playwright] Could not auto-detect URL. Check your Gumroad dashboard.")
            print(f"[playwright] Dashboard: https://app.gumroad.com/products")

        print("[playwright] Done. Browser will close in 10 seconds...")
        time.sleep(10)
        browser.close()


if __name__ == "__main__":
    create_product()
