#!/usr/bin/env python3
"""
gumroad_products.py

Local-Em's tool for managing Gumroad products autonomously.
Uses the Gumroad API v2 with GUMROAD_ACCESS_TOKEN from environment.

Usage (from local_em.py response or standalone):
    TOOL: gumroad_list_products()
    TOOL: gumroad_create_product("Title", "Description", price_cents, "content here")
    TOOL: gumroad_update_product("product_id", description="new desc", price_cents=999)

Credentials: GUMROAD_ACCESS_TOKEN in Windows environment variables (already set).
"""

import os
import sys
import json
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timezone

# Force UTF-8 output for Windows terminals
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr.encoding and sys.stderr.encoding.lower() != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

API_BASE = "https://api.gumroad.com/v2"


def load_token() -> str:
    token = os.environ.get("GUMROAD_ACCESS_TOKEN")
    if not token:
        # Fallback: check .env
        env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
        if os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("GUMROAD_ACCESS_TOKEN="):
                        token = line.split("=", 1)[1].strip().strip('"').strip("'")
                        break
    if not token:
        raise RuntimeError("GUMROAD_ACCESS_TOKEN not found in environment or .env")
    return token


def gumroad_request(method: str, endpoint: str, data: dict = None) -> dict:
    token = load_token()
    url = f"{API_BASE}{endpoint}"

    if method == "GET":
        if data:
            url += "?" + urllib.parse.urlencode(data)
        req = urllib.request.Request(url, method="GET")
    else:
        payload = data or {}
        payload["access_token"] = token
        encoded = urllib.parse.urlencode(payload).encode()
        req = urllib.request.Request(url, data=encoded, method=method)

    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")

    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        err_body = e.read().decode()
        raise RuntimeError(f"Gumroad API {method} {endpoint} -> {e.code}: {err_body}")


def list_products() -> list:
    """Return all products in the Gumroad account."""
    result = gumroad_request("GET", "/products")
    products = result.get("products", [])
    print(f"[gumroad] Found {len(products)} product(s):")
    for p in products:
        price = p.get('price', 0) / 100
        sales = p.get('sales_count', 0)
        print(f"  - {p['name']} | ${price:.2f} | {sales} sales | id: {p['id']}")
    return products


def create_product(name: str, description: str, price_cents: int, content: str = "") -> dict:
    """
    Create a new Gumroad product.
    price_cents: price in cents (e.g. 900 = $9.00, 0 = free)
    content: the actual product content (will be stored as description if no file upload)
    """
    data = {
        "name": name,
        "description": f"{description}\n\n---\n\n{content}" if content else description,
        "price": price_cents,
    }
    result = gumroad_request("POST", "/products", data)
    product = result.get("product", {})
    print(f"[gumroad] Created: {product.get('name')} | id: {product.get('id')} | ${price_cents/100:.2f}")
    print(f"[gumroad] URL: {product.get('short_url', 'N/A')}")
    return product


def update_product(product_id: str, name: str = None, description: str = None,
                   price_cents: int = None, published: bool = None) -> dict:
    """Update an existing Gumroad product."""
    data = {}
    if name is not None:
        data["name"] = name
    if description is not None:
        data["description"] = description
    if price_cents is not None:
        data["price"] = price_cents
    if published is not None:
        data["published"] = str(published).lower()
    result = gumroad_request("PUT", f"/products/{product_id}", data)
    product = result.get("product", {})
    print(f"[gumroad] Updated: {product.get('name')} | id: {product_id}")
    return product


def get_sales() -> list:
    """Return recent sales data."""
    result = gumroad_request("GET", "/sales")
    sales = result.get("sales", [])
    total = sum(s.get("price", 0) for s in sales) / 100
    print(f"[gumroad] {len(sales)} recent sale(s) | Total: ${total:.2f}")
    for s in sales[:5]:
        print(f"  - {s.get('product_name')} | ${s.get('price',0)/100:.2f} | {s.get('created_at', '')}")
    return sales


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Gumroad product manager for Em")
    parser.add_argument("action", choices=["list", "sales", "create"], help="Action to perform")
    parser.add_argument("--name", help="Product name (for create)")
    parser.add_argument("--description", help="Product description (for create)")
    parser.add_argument("--price", type=int, default=900, help="Price in cents (default: 900 = $9.00)")
    parser.add_argument("--content", help="Product content text (for create)")
    args = parser.parse_args()

    if args.action == "list":
        list_products()
    elif args.action == "sales":
        get_sales()
    elif args.action == "create":
        if not args.name:
            print("ERROR: --name required for create", file=sys.stderr)
            sys.exit(1)
        create_product(
            name=args.name,
            description=args.description or "",
            price_cents=args.price,
            content=args.content or ""
        )
