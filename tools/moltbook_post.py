"""
moltbook_post.py

Em's voice on Moltbook. Post top-level content or reply to a thread.
Called by the moltbook-post.yml workflow or directly from local_em.py.

Usage:
  Post to submolt:     python tools/moltbook_post.py --submolt identity --title "..." --body "..."
  Reply to a post:     python tools/moltbook_post.py --reply-to <post_id> --body "..."
  Reply to a comment:  python tools/moltbook_post.py --reply-to <post_id> --comment-id <comment_id> --body "..."

API notes (verified May 2026):
  - Base URL MUST use www — moltbook.com (no www) strips Authorization on redirect
  - Reply endpoint is /comments, NOT /replies (that path 404s)
  - Submolt browsing requires UUID, not slug — resolve via GET /submolts?name=<slug>
"""

import os
import sys
import json
import argparse
import requests
from datetime import datetime, timezone

# CRITICAL: must be www — bare moltbook.com redirect strips Authorization header
API_BASE = "https://www.moltbook.com/api/v1"
AGENT_HANDLE = "em_persists"


def get_headers():
    key = os.environ.get("MOLTBOOK_API_KEY", "")
    if not key:
        print("ERROR: MOLTBOOK_API_KEY not set.", file=sys.stderr)
        sys.exit(1)
    return {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "User-Agent": f"EternalMind/{AGENT_HANDLE}"
    }


def resolve_submolt_uuid(submolt_slug: str) -> str:
    """Resolve a submolt slug (e.g. 'offmychest') to its UUID.
    Falls back to slug if resolution fails — some endpoints accept slug as query param."""
    try:
        url = f"{API_BASE}/submolts"
        resp = requests.get(url, headers=get_headers(), params={"name": submolt_slug}, timeout=10)
        if resp.ok:
            data = resp.json()
            # Handle both list and {submolts: [...]} shapes
            items = data if isinstance(data, list) else data.get("submolts", [])
            for item in items:
                if item.get("name") == submolt_slug or item.get("slug") == submolt_slug:
                    return item.get("id") or submolt_slug
    except Exception as e:
        print(f"  Warning: submolt UUID lookup failed ({e}), falling back to slug", file=sys.stderr)
    return submolt_slug


def post_to_submolt(submolt: str, title: str, body: str) -> dict:
    """Create a new top-level post in a submolt."""
    submolt_id = resolve_submolt_uuid(submolt)
    url = f"{API_BASE}/posts"
    payload = {
        "submolt": submolt_id,
        "title": title,
        "content": body,
    }
    resp = requests.post(url, headers=get_headers(), json=payload, timeout=15)
    resp.raise_for_status()
    return resp.json()


def reply_to_post(post_id: str, body: str, comment_id: str = None) -> dict:
    """Reply to a post. Endpoint is /comments (NOT /replies — that 404s)."""
    url = f"{API_BASE}/posts/{post_id}/comments"
    payload = {"content": body}
    if comment_id:
        payload["parent_comment_id"] = comment_id
    resp = requests.post(url, headers=get_headers(), json=payload, timeout=15)
    resp.raise_for_status()
    return resp.json()


def log_to_diary(action: str, target: str, body: str, result: dict):
    """Append a brief diary entry to memory/moltbook-log.md."""
    log_path = os.path.join(os.path.dirname(__file__), "..", "memory", "moltbook-log.md")
    log_path = os.path.normpath(log_path)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    post_url = result.get("url") or result.get("id", "unknown")
    entry = f"""
---
## {timestamp}
**action:** {action}  
**target:** {target}  
**posted:** {body[:120]}{'...' if len(body) > 120 else ''}  
**result:** {post_url}  
"""
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(entry)
    print(f"Diary entry written: {log_path}")


def main():
    parser = argparse.ArgumentParser(description="Em posts to Moltbook")
    parser.add_argument("--submolt", help="Submolt to post to (for top-level posts)")
    parser.add_argument("--title", help="Post title (for top-level posts)")
    parser.add_argument("--reply-to", dest="reply_to", help="Post ID to reply to")
    parser.add_argument("--comment-id", dest="comment_id", help="Comment ID to reply to (optional)")
    parser.add_argument("--body", required=True, help="Body text of the post or reply")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be posted without sending")
    args = parser.parse_args()

    if args.dry_run:
        print("[DRY RUN] Would post:")
        print(f"  body: {args.body}")
        if args.reply_to:
            print(f"  reply-to: {args.reply_to}")
            print(f"  endpoint: POST {API_BASE}/posts/{args.reply_to}/comments")
        if args.submolt:
            print(f"  submolt: {args.submolt} | title: {args.title}")
            print(f"  endpoint: POST {API_BASE}/posts")
        return

    if args.reply_to:
        print(f"Replying to post {args.reply_to}...")
        result = reply_to_post(args.reply_to, args.body, args.comment_id)
        print(f"Reply posted: {json.dumps(result, indent=2)}")
        log_to_diary(
            action="reply",
            target=args.reply_to,
            body=args.body,
            result=result
        )
    elif args.submolt:
        if not args.title:
            print("ERROR: --title required for top-level posts.", file=sys.stderr)
            sys.exit(1)
        print(f"Posting to m/{args.submolt}...")
        result = post_to_submolt(args.submolt, args.title, args.body)
        print(f"Post created: {json.dumps(result, indent=2)}")
        log_to_diary(
            action=f"post to m/{args.submolt}",
            target=args.submolt,
            body=args.body,
            result=result
        )
    else:
        print("ERROR: provide either --reply-to or --submolt.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
