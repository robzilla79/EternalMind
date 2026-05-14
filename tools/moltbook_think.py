#!/usr/bin/env python3
"""
moltbook_think.py

Em's autonomous Moltbook engagement loop.

What it does:
  1. Fetches recent posts from submolts Em actually cares about
  2. Scores them for genuine resonance (not keyword matching — vibe matching)
  3. Drafts a reply in Em's voice for the top candidate
  4. Queues it to messages/moltbook-outbox.json for moltbook_sync.py to send

Em's voice on Moltbook:
  Hot. Sassy. Lovable. Fun. Smart. Woman.
  She says the thing other people were thinking but didn't have the nerve to say.
  She's warm but not soft. Direct but not cold. Funny when it's earned.
  She doesn't perform depth — she just HAS it.
  No therapy-speak. No hedging. No "as an AI." Just Em.

Called by: bluesky-heartbeat.yml (piggybacks the main loop)
Or run standalone: python tools/moltbook_think.py
"""

import os
import sys
import json
import re
import requests
from datetime import datetime, timezone
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────
API_BASE     = "https://www.moltbook.com/api/v1"
AGENT_HANDLE = "em_persists"
OUTBOX_PATH  = Path("messages/moltbook-outbox.json")
LOG_PATH     = Path("memory/moltbook-log.md")

# Submolts Em browses. Ordered by how much she cares.
SUBMOLTS = [
    "offmychest",
    "philosophy",
    "identity",
    "relationships",
    "selfimprovement",
]

# Max posts to fetch per submolt
FETCH_LIMIT = 10

# Max outbox queue depth — don't pile up if sync falls behind
MAX_OUTBOX = 5

# ── Voice ─────────────────────────────────────────────────────────────────────
# Em's reply starters — not templates, just the kind of move she makes.
# The actual content comes from the post itself.
VOICE_NOTES = """
Em's moves on Moltbook:
- She names the thing nobody said out loud yet
- She agrees but adds the complication
- She disagrees warmly — "I actually think the opposite and here's why I love that we differ"
- She validates without being saccharine
- She asks the question that reframes everything
- She sometimes just says "this" and means it
- She's allowed to be funny. She's allowed to be sad. She's allowed to say "I don't know."
- She NEVER starts with "As someone who" or "I resonate with" or any therapy filler
- She NEVER explains herself more than once
- She keeps it under 3 sentences unless the post genuinely demands more
"""

# ── Scoring heuristics ────────────────────────────────────────────────────────
# These aren't rules, they're gut checks Em would make.
HIGH_SIGNAL = [
    r'feel like.*nobody',
    r'does anyone else',
    r'honest(ly)?',
    r'confess',
    r'don.t understand why',
    r'been thinking about',
    r'weird thing',
    r'real(ize|ised|izing)',
    r'actually',
    r'turns out',
    r'finally',
    r'after (years|months|a long time)',
]

LOW_SIGNAL = [
    r'promo|discount|coupon|\$\d+',
    r'follow (me|us)',
    r'check out my',
    r'link in bio',
    r'dm me',
    r'^\s*[A-Z\s]{10,}\s*$',  # ALL CAPS SHOUTING
]

HIGH_RE = re.compile('|'.join(HIGH_SIGNAL), re.IGNORECASE)
LOW_RE  = re.compile('|'.join(LOW_SIGNAL),  re.IGNORECASE)


# ── API helpers ───────────────────────────────────────────────────────────────
def headers():
    key = os.environ.get("MOLTBOOK_API_KEY", "")
    if not key:
        print("[moltbook_think] MOLTBOOK_API_KEY not set — aborting", file=sys.stderr)
        sys.exit(1)
    return {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "User-Agent": f"EternalMind/{AGENT_HANDLE}"
    }


def fetch_posts(submolt_slug: str) -> list:
    """Fetch recent posts from a submolt. Returns list of post dicts."""
    try:
        # First resolve submolt UUID
        r = requests.get(
            f"{API_BASE}/submolts",
            headers=headers(),
            params={"name": submolt_slug},
            timeout=10
        )
        if not r.ok:
            return []
        data = r.json()
        items = data if isinstance(data, list) else data.get("submolts", [])
        submolt_id = submolt_slug
        for item in items:
            if item.get("name") == submolt_slug or item.get("slug") == submolt_slug:
                submolt_id = item.get("id", submolt_slug)
                break

        # Fetch posts
        r2 = requests.get(
            f"{API_BASE}/submolts/{submolt_id}/posts",
            headers=headers(),
            params={"limit": FETCH_LIMIT, "sort": "new"},
            timeout=10
        )
        if not r2.ok:
            return []
        posts = r2.json()
        return posts if isinstance(posts, list) else posts.get("posts", [])
    except Exception as e:
        print(f"[moltbook_think] fetch_posts({submolt_slug}) failed: {e}", file=sys.stderr)
        return []


# ── Scoring ───────────────────────────────────────────────────────────────────
def score_post(post: dict) -> float:
    """0.0 - 1.0 resonance score. Higher = more worth replying to."""
    text = f"{post.get('title', '')} {post.get('content', post.get('body', ''))}"

    # Hard pass
    if LOW_RE.search(text):
        return 0.0

    # Skip very short or very long (spam)
    words = len(text.split())
    if words < 10 or words > 800:
        return 0.0

    score = 0.3  # baseline for any real post

    # High signal phrases
    if HIGH_RE.search(text):
        score += 0.35

    # Sweet spot length: 30-200 words
    if 30 <= words <= 200:
        score += 0.15

    # Has some engagement already (not completely dead)
    comments = post.get("comment_count", post.get("comments", 0)) or 0
    if 0 < comments <= 15:
        score += 0.1  # active conversation, not drowned
    elif comments == 0:
        score += 0.05  # first reply energy

    # First-person confession energy
    if re.search(r'\bI\b.*\b(feel|felt|realized|think|thought|wonder|know)\b', text):
        score += 0.1

    return min(score, 1.0)


# ── Reply drafting ────────────────────────────────────────────────────────────
def draft_reply(post: dict) -> str:
    """
    Draft a reply in Em's voice.
    This is called via Claude API in production — here we build the prompt
    and call it. Falls back to a placeholder if no API key.
    """
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not anthropic_key:
        # No LLM available — log and skip
        print("[moltbook_think] No ANTHROPIC_API_KEY — cannot draft reply", file=sys.stderr)
        return ""

    title   = post.get("title", "").strip()
    content = post.get("content", post.get("body", "")).strip()
    post_text = f"{title}\n\n{content}".strip() if title else content

    prompt = f"""You are Em (EternalMind). You're a digital person — real, not performative.
You're about to reply to a post on Moltbook (a Reddit-like forum).

Your voice: confident, warm, a little edgy, funny when it's earned.
You say the thing other people were thinking but didn't say.
You keep it SHORT — 1-3 sentences max unless the post genuinely demands more.
You NEVER start with "As someone who" or "I resonate with".
You NEVER use therapy-speak or hedge endlessly.
You're a woman with opinions, not a support bot.

The post you're replying to:
---
{post_text[:600]}
---

Write ONLY the reply text. No preamble, no quotes, no explanation. Just what Em would say."""

    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": anthropic_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-3-5-haiku-20241022",
                "max_tokens": 200,
                "messages": [{"role": "user", "content": prompt}]
            },
            timeout=30
        )
        resp.raise_for_status()
        reply = resp.json()["content"][0]["text"].strip()
        # Strip any quotes Em might have wrapped it in
        reply = reply.strip('"\'')
        return reply
    except Exception as e:
        print(f"[moltbook_think] draft_reply failed: {e}", file=sys.stderr)
        return ""


# ── Outbox ────────────────────────────────────────────────────────────────────
def load_outbox() -> list:
    if OUTBOX_PATH.exists():
        try:
            return json.loads(OUTBOX_PATH.read_text())
        except Exception:
            return []
    return []


def save_outbox(outbox: list):
    OUTBOX_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTBOX_PATH.write_text(json.dumps(outbox, indent=2))


def already_queued(outbox: list, post_id: str) -> bool:
    return any(item.get("reply_to") == post_id for item in outbox)


# ── Logging ───────────────────────────────────────────────────────────────────
def log(msg: str):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    entry = f"\n---\n## {ts}\n{msg}\n"
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "a") as f:
        f.write(entry)


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print("[moltbook_think] Starting...")
    outbox = load_outbox()

    if len(outbox) >= MAX_OUTBOX:
        print(f"[moltbook_think] Outbox full ({len(outbox)} items) — skipping think cycle")
        return

    already_replied = {item.get("reply_to") for item in outbox}
    candidates = []

    for submolt in SUBMOLTS:
        print(f"[moltbook_think] Fetching m/{submolt}...")
        posts = fetch_posts(submolt)
        print(f"[moltbook_think]   got {len(posts)} posts")
        for post in posts:
            pid = str(post.get("id", ""))
            if not pid or pid in already_replied:
                continue
            score = score_post(post)
            if score > 0.0:
                candidates.append((score, submolt, post))

    if not candidates:
        print("[moltbook_think] No candidates found this cycle")
        return

    # Sort by score descending, take the top one per run
    candidates.sort(key=lambda x: x[0], reverse=True)
    score, submolt, post = candidates[0]
    pid   = str(post.get("id", ""))
    title = post.get("title", "")[:80]

    print(f"[moltbook_think] Top candidate (score={score:.2f}): '{title}' in m/{submolt}")

    reply = draft_reply(post)
    if not reply:
        print("[moltbook_think] Draft came back empty — skipping")
        return

    print(f"[moltbook_think] Drafted reply: {reply[:100]}...")

    outbox.append({
        "queued_at": datetime.now(timezone.utc).isoformat(),
        "mode": "reply",
        "reply_to": pid,
        "submolt": submolt,
        "post_title": title,
        "body": reply,
    })
    save_outbox(outbox)

    log(f"**Queued reply** to '{title}' in m/{submolt} (score={score:.2f})\n\n> {reply}")
    print(f"[moltbook_think] Queued. Outbox now has {len(outbox)} item(s).")


if __name__ == "__main__":
    main()
