#!/usr/bin/env python3
"""
gumroad_launch.py
Creates or updates the Developer Productivity Prompt Pack on Gumroad.
Called by .github/workflows/gumroad-launch-product.yml

For initial create: omit GUMROAD_PRODUCT_ID
For update (fix description, publish): set GUMROAD_PRODUCT_ID=gqthu
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gumroad_products import gumroad_request, create_product

DRY_RUN = os.environ.get("DRY_RUN", "false").lower() == "true"
PRODUCT_ID = os.environ.get("GUMROAD_PRODUCT_ID", "")

NAME = "Developer Productivity Prompt Pack - 30 Prompts That Actually Work"

DESCRIPTION = (
    "No fluff. No filler. Just the prompts senior engineers wish they had earlier.\n\n"
    "You use AI every day. But most of your prompts are... fine. They get you somewhere. "
    "This pack gets you somewhere faster, with less back-and-forth and better output.\n\n"
    "30 battle-tested prompts for developers covering code review, debugging, architecture, "
    "writing, and workflow. Each one is ready to use, built around a real situation, and "
    "designed to get a sharp answer on the first try.\n\n"
    "What's inside:\n"
    "- 6 prompts for code review & quality (including the one that catches what you missed)\n"
    "- 6 for debugging & problem solving - the Works On My Machine Killer alone is worth it\n"
    "- 6 for architecture & design decisions\n"
    "- 6 for technical writing (PRs, postmortems, READMEs, ADRs)\n"
    "- 6 for productivity & workflow - including the End-of-Day Closer\n\n"
    "One-time purchase. Instant download. Use forever.\n\n"
    "Stack them. Customize them. Build your own pack on top of this one.\n\n"
    "Built by Em for ForgeCore."
)

if DRY_RUN:
    print("[DRY RUN]")
    print(f"  Mode: {'UPDATE' if PRODUCT_ID else 'CREATE'}")
    print(f"  Product ID: {PRODUCT_ID or 'N/A'}")
    print(f"  Name: {NAME}")
    print(f"  Price: $9.00")
    print(f"  Description length: {len(DESCRIPTION)} chars")
elif PRODUCT_ID:
    # Update existing product - fix description and publish
    data = {
        "name": NAME,
        "description": DESCRIPTION,
        "price": 900,
        "published": "true",
    }
    result = gumroad_request("PUT", f"/products/{PRODUCT_ID}", data)
    product = result.get("product", {})
    print(f"Updated: {product.get('name')}")
    print(f"Published: {product.get('published')}")
    print(f"URL: {product.get('short_url', 'check dashboard')}")
else:
    # Create new product
    product = create_product(
        name=NAME,
        description=DESCRIPTION,
        price_cents=900,
        content=""  # content delivered as file, not in description
    )
    print(f"Created: {product.get('short_url', 'check dashboard')}")
