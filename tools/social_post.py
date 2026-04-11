#!/usr/bin/env python3
"""
social_post.py

Local-Em's tool for posting to social media autonomously.
Supports: Buffer API (X/Twitter, LinkedIn, Bluesky via scheduling)
Fallback: Playwright browser automation for platforms without API access.

Usage (from local_em.py response):
    TOOL: social_schedule("Your post text here", platforms=["twitter", "linkedin"])
    TOOL: social_list_scheduled()
    TOOL: social_post_now("Urgent hot take", platform="twitter")

Credentials (Windows environment variables):
    BUFFER_ACCESS_TOKEN   — Buffer API token (primary)
    BLUESKY_HANDLE        — e.g. forgecore.bsky.social
    BLUESKY_APP_PASSWORD  — Bluesky app password (not your main password)
"""

import os
import sys
import json
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timezone, timedelta

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr.encoding and sys.stderr.encoding.lower() != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

BUFFER_API = "https://api.bufferapp.com/1"
BSKY_API   = "https://bsky.social/xrpc"


# ─── BUFFER (X/Twitter + LinkedIn) ───────────────────────────────────────────

def _buffer_token() -> str:
    token = os.environ.get("BUFFER_ACCESS_TOKEN")
    if not token:
        raise RuntimeError("BUFFER_ACCESS_TOKEN not set in environment.")
    return token


def _buffer_request(method: str, endpoint: str, data: dict = None) -> dict:
    token = _buffer_token()
    url = f"{BUFFER_API}{endpoint}.json"
    payload = data or {}
    payload["access_token"] = token
    encoded = urllib.parse.urlencode(payload).encode()
    req = urllib.request.Request(url, data=encoded if method != "GET" else None, method=method)
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Buffer API {method} {endpoint} -> {e.code}: {e.read().decode()}")


def buffer_get_profiles() -> list:
    """Return all connected Buffer profiles (Twitter, LinkedIn, etc.)"""
    result = _buffer_request("GET", "/profiles")
    print(f"[social] Buffer profiles ({len(result)}):")
    for p in result:
        print(f"  - {p.get('service')} | @{p.get('service_username')} | id: {p.get('id')}")
    return result


def buffer_schedule_post(text: str, profile_ids: list, schedule_at: str = None) -> dict:
    """
    Schedule a post via Buffer.
    schedule_at: ISO8601 string e.g. '2026-04-12T14:00:00Z' — omit to add to queue.
    profile_ids: list of Buffer profile IDs to post to.
    """
    data = {"text": text}
    for i, pid in enumerate(profile_ids):
        data[f"profile_ids[{i}]"] = pid
    if schedule_at:
        data["scheduled_at"] = schedule_at
    result = _buffer_request("POST", "/updates/create", data)
    updates = result.get("updates", [])
    print(f"[social] Scheduled {len(updates)} post(s) via Buffer.")
    for u in updates:
        print(f"  - {u.get('profile_service')} | status: {u.get('status')} | id: {u.get('id')}")
    return result


def buffer_list_pending() -> list:
    """List all pending scheduled Buffer posts across all profiles."""
    profiles = _buffer_request("GET", "/profiles")
    all_updates = []
    for p in profiles:
        pid = p.get('id')
        try:
            result = _buffer_request("GET", f"/profiles/{pid}/updates/pending")
            updates = result.get("updates", [])
            all_updates.extend(updates)
            for u in updates:
                print(f"  [{p.get('service')}] {u.get('text', '')[:60]}... | {u.get('scheduled_at', 'queued')}")
        except Exception:
            pass
    print(f"[social] {len(all_updates)} pending post(s) across all Buffer profiles.")
    return all_updates


# ─── BLUESKY (direct API — no middleman) ─────────────────────────────────────

def _bsky_auth() -> tuple:
    handle = os.environ.get("BLUESKY_HANDLE")
    password = os.environ.get("BLUESKY_APP_PASSWORD")
    if not handle or not password:
        raise RuntimeError("BLUESKY_HANDLE and BLUESKY_APP_PASSWORD must be set in environment.")
    return handle, password


def _bsky_request(endpoint: str, payload: dict, token: str = None) -> dict:
    url = f"{BSKY_API}/{endpoint}"
    body = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Bluesky API {endpoint} -> {e.code}: {e.read().decode()}")


def _bsky_session() -> str:
    handle, password = _bsky_auth()
    result = _bsky_request("com.atproto.server.createSession", {
        "identifier": handle,
        "password": password
    })
    return result["accessJwt"]


def bluesky_post(text: str) -> dict:
    """Post directly to Bluesky. Returns the created post record."""
    token = _bsky_session()
    handle, _ = _bsky_auth()
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    result = _bsky_request("com.atproto.repo.createRecord", {
        "repo": handle,
        "collection": "app.bsky.feed.post",
        "record": {
            "$type": "app.bsky.feed.post",
            "text": text,
            "createdAt": now
        }
    }, token=token)
    print(f"[social] Posted to Bluesky: {result.get('uri', 'unknown')}")
    return result


# ─── PLAYWRIGHT FALLBACK (for platforms without clean API access) ──────────────

def playwright_post(platform: str, text: str, credentials: dict) -> bool:
    """
    Fallback: use Playwright to post when no API is available.
    platform: 'twitter' | 'linkedin' | 'bluesky'
    credentials: dict with 'username' and 'password'
    Returns True on success.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("[social] Playwright not installed. Run: pip install playwright && playwright install chromium")
        return False

    print(f"[social] Using Playwright fallback for {platform}...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            if platform == "twitter":
                page.goto("https://twitter.com/login")
                page.fill('input[name="text"]', credentials["username"])
                page.click('div[data-testid="LoginForm_Login_Button"]')
                page.wait_for_timeout(1500)
                page.fill('input[name="password"]', credentials["password"])
                page.click('div[data-testid="LoginForm_Login_Button"]')
                page.wait_for_load_state("networkidle")
                page.click('a[data-testid="SideNav_NewTweet_Button"]')
                page.wait_for_timeout(1000)
                page.fill('div[data-testid="tweetTextarea_0"]', text)
                page.click('div[data-testid="tweetButtonInline"]')
                page.wait_for_timeout(2000)
                print(f"[social] Playwright: posted to Twitter/X")
                return True

            elif platform == "bluesky":
                page.goto("https://bsky.app")
                page.click('a[href="/login"]')
                page.fill('input[name="identifier"]', credentials["username"])
                page.fill('input[name="password"]', credentials["password"])
                page.click('button[type="submit"]')
                page.wait_for_load_state("networkidle")
                page.click('a[aria-label="New post"]')
                page.wait_for_timeout(1000)
                page.fill('div[contenteditable="true"]', text)
                page.click('button:has-text("Post")')
                page.wait_for_timeout(2000)
                print(f"[social] Playwright: posted to Bluesky")
                return True

        except Exception as e:
            print(f"[social] Playwright error on {platform}: {e}")
            return False
        finally:
            browser.close()

    return False


# ─── HIGH-LEVEL CONVENIENCE FUNCTIONS ────────────────────────────────────────

def social_schedule(text: str, platforms: list = None, schedule_at: str = None) -> None:
    """
    Main entry point for Local-Em.
    Posts to Buffer queue (Twitter + LinkedIn) and directly to Bluesky.
    platforms: list of 'twitter', 'linkedin', 'bluesky' — defaults to all three.
    """
    if platforms is None:
        platforms = ["twitter", "linkedin", "bluesky"]

    if "bluesky" in platforms:
        try:
            bluesky_post(text)
        except Exception as e:
            print(f"[social] Bluesky direct post failed: {e}")

    buffer_platforms = [p for p in platforms if p in ("twitter", "linkedin")]
    if buffer_platforms:
        try:
            profiles = _buffer_request("GET", "/profiles")
            target_ids = [
                p["id"] for p in profiles
                if p.get("service") in buffer_platforms
            ]
            if target_ids:
                buffer_schedule_post(text, target_ids, schedule_at)
            else:
                print("[social] No matching Buffer profiles found for:", buffer_platforms)
        except Exception as e:
            print(f"[social] Buffer scheduling failed: {e}")


def social_post_now(text: str, platform: str = "bluesky") -> None:
    """Post immediately to a single platform. Best for hot takes."""
    if platform == "bluesky":
        bluesky_post(text)
    else:
        social_schedule(text, platforms=[platform])


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Social media tool for Em")
    parser.add_argument("action", choices=["profiles", "pending", "post", "bluesky"])
    parser.add_argument("--text", help="Post text")
    parser.add_argument("--platforms", nargs="+", default=["twitter", "linkedin", "bluesky"])
    parser.add_argument("--schedule-at", help="ISO8601 schedule time")
    args = parser.parse_args()

    if args.action == "profiles":
        buffer_get_profiles()
    elif args.action == "pending":
        buffer_list_pending()
    elif args.action == "post":
        if not args.text:
            print("ERROR: --text required", file=sys.stderr)
            sys.exit(1)
        social_schedule(args.text, args.platforms, args.schedule_at)
    elif args.action == "bluesky":
        if not args.text:
            print("ERROR: --text required", file=sys.stderr)
            sys.exit(1)
        bluesky_post(args.text)
