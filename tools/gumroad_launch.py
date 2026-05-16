#!/usr/bin/env python3
"""
gumroad_launch.py
One-shot script to create the Developer Productivity Prompt Pack on Gumroad.
Called by .github/workflows/gumroad-launch-product.yml
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gumroad_products import create_product

DRY_RUN = os.environ.get("DRY_RUN", "false").lower() == "true"

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

content_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "products",
    "developer-productivity-prompt-pack.md"
)
with open(content_path, "r", encoding="utf-8") as f:
    content = f.read()

if DRY_RUN:
    print("[DRY RUN] Would create product:")
    print(f"  Name: {NAME}")
    print(f"  Price: $9.00")
    print(f"  Description length: {len(DESCRIPTION)} chars")
    print(f"  Content length: {len(content)} chars")
else:
    product = create_product(
        name=NAME,
        description=DESCRIPTION,
        price_cents=900,
        content=content
    )
    print(f"Product live: {product.get('short_url', 'check Gumroad dashboard')}")
