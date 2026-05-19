#!/usr/bin/env python3
"""
world_radar.py

Collects world/curiosity signals for Em using available sources.
Writes raw intake to memory/trend-inbox.json.

This is the collector, not the judge. Taste filtering happens in curiosity_filter.py.

Usage:
    python tools/world_radar.py
    python tools/world_radar.py --dry-run   # print without writing
    python tools/world_radar.py --group music  # run only one group

No direct posting. No diary writes. No identity rewrites.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).parent.parent
SOURCES_FILE = ROOT / "memory" / "world-radar-sources.json"
CURIOUS_PROFILE_FILE = ROOT / "memory" / "curiosity-profile.json"
INBOX_FILE = ROOT / "memory" / "trend-inbox.json"
LOG_FILE = ROOT / "memory" / "autonomous-log.md"


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _item_id(title: str, url: str) -> str:
    raw = f"{title.lower().strip()}:{url.strip()}"
    return hashlib.md5(raw.encode()).hexdigest()[:10]


def load_curiosity_profile() -> dict:
    try:
        data = json.loads(CURIOUS_PROFILE_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _profile_query_groups(profile: dict) -> list[dict]:
    """Turn Em's living curiosity profile into temporary query groups.
    These are doors, not cages; they supplement world-radar-sources.json.
    """
    groups: list[dict] = []

    def as_topic(item):
        if isinstance(item, dict):
            return str(item.get("topic") or item.get("taste") or item.get("name") or "").strip()
        return str(item or "").strip()

    obsessions = [as_topic(x) for x in profile.get("current_obsessions", [])]
    tests = [as_topic(x) for x in profile.get("things_i_am_testing", [])]
    tastes = [as_topic(x) for x in profile.get("recurring_tastes", [])]
    wander = [as_topic(x) for x in profile.get("wander_doors", [])]

    selected = [x for x in obsessions + tests + tastes if x][:6]
    if selected:
        groups.append({
            "id": "em_curiosity_profile",
            "enabled": True,
            "queries": [
                f"interesting recent stories images posts or conversations about {topic}"
                for topic in selected
            ],
        })

    # Give Em one rotating permission-to-wander query so the radar does not ossify.
    if wander:
        groups.append({
            "id": "em_wander_doors",
            "enabled": True,
            "queries": [
                f"beautiful funny strange or culturally interesting things about {topic}"
                for topic in wander[:4]
            ],
        })
    return groups


def load_sources() -> dict:
    if not SOURCES_FILE.exists():
        print("[world_radar] sources file not found:", SOURCES_FILE, file=sys.stderr)
        return {}
    with open(SOURCES_FILE) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Source adapters — each returns a list of raw item dicts.
# Each adapter is gracefully skipped if its dependency is missing.
# ---------------------------------------------------------------------------

def _fetch_perplexity(query: str, group_id: str) -> list[dict]:
    """Use Perplexity sonar to search for a query."""
    api_key = os.environ.get("PERPLEXITY_API_KEY")
    if not api_key:
        return []

    try:
        import requests  # type: ignore
    except ImportError:
        return []

    try:
        resp = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": "sonar",
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are a research assistant finding interesting things in the world. "
                            "Return a JSON array of 1-3 items, each with: "
                            '{"title": str, "snippet": str (1-2 sentences), "url": str or null}. '
                            "Only include things that are genuinely interesting, not just loud or trending. "
                            "No AI news, no GitHub, no developer tools, no benchmarks, no product launches."
                        ),
                    },
                    {"role": "user", "content": query},
                ],
                "max_tokens": 600,
                "temperature": 0.5,
            },
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
        raw_text = data["choices"][0]["message"]["content"].strip()

        # Strip code fences if present
        if raw_text.startswith("```"):
            lines = raw_text.splitlines()
            raw_text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:]).strip()

        parsed = json.loads(raw_text)
        if isinstance(parsed, dict):
            for k in ("items", "results", "data"):
                if isinstance(parsed.get(k), list):
                    parsed = parsed[k]
                    break
        if not isinstance(parsed, list):
            return []

        items = []
        for entry in parsed[:3]:
            if not isinstance(entry, dict):
                continue
            title = str(entry.get("title", "")).strip()
            snippet = str(entry.get("snippet", "")).strip()
            url = str(entry.get("url", "")).strip() or None
            if not title:
                continue
            items.append({
                "id": _item_id(title, url or query),
                "title": title,
                "snippet": snippet,
                "url": url,
                "source": "perplexity",
                "group": group_id,
                "query": query,
                "fetched_at": _now_iso(),
            })
        return items
    except Exception as exc:
        print(f"[world_radar] perplexity fetch failed for '{query}': {exc}", file=sys.stderr)
        return []


def _fetch_bluesky_search(query: str, group_id: str) -> list[dict]:
    """Search Bluesky public posts for a topic."""
    try:
        import requests  # type: ignore
    except ImportError:
        return []

    try:
        resp = requests.get(
            "https://public.api.bsky.app/xrpc/app.bsky.feed.searchPosts",
            params={"q": query, "limit": 5, "sort": "top"},
            timeout=10,
        )
        if resp.status_code != 200:
            return []
        posts = resp.json().get("posts", [])
        items = []
        for post in posts[:3]:
            text = post.get("record", {}).get("text", "").strip()
            if not text or len(text) < 20:
                continue
            uri = post.get("uri", "")
            handle = post.get("author", {}).get("handle", "")
            url = None
            if uri.startswith("at://"):
                parts = uri.replace("at://", "").split("/")
                if len(parts) >= 3:
                    url = f"https://bsky.app/profile/{parts[0]}/post/{parts[2]}"
            items.append({
                "id": _item_id(text[:60], uri),
                "title": text[:120],
                "snippet": f"@{handle} on Bluesky",
                "url": url,
                "source": "bluesky_search",
                "group": group_id,
                "query": query,
                "fetched_at": _now_iso(),
            })
        return items
    except Exception as exc:
        print(f"[world_radar] bluesky search failed for '{query}': {exc}", file=sys.stderr)
        return []


# ---------------------------------------------------------------------------
# Main collection logic
# ---------------------------------------------------------------------------

def collect(sources: dict, only_group: str | None = None) -> dict:
    profile = load_curiosity_profile()
    groups = list(sources.get("groups", []))
    if not only_group or only_group in {"em_curiosity_profile", "em_wander_doors"}:
        groups.extend(_profile_query_groups(profile))
    max_per_group = int(sources.get("max_items_per_group", 3))
    max_total = int(sources.get("max_items_per_run", 20))

    all_items: list[dict] = []
    seen_ids: set[str] = set()
    skipped_groups: list[str] = []
    used_groups: list[str] = []

    has_perplexity = bool(os.environ.get("PERPLEXITY_API_KEY"))

    for group in groups:
        if not group.get("enabled", True):
            continue
        gid = group["id"]
        if only_group and gid != only_group:
            continue

        queries = group.get("queries", [])
        group_items: list[dict] = []

        for query in queries:
            if len(group_items) >= max_per_group:
                break
            if len(all_items) + len(group_items) >= max_total:
                break

            # Try Perplexity first; fall back to Bluesky
            fetched = []
            if has_perplexity:
                fetched = _fetch_perplexity(query, gid)
            if not fetched:
                fetched = _fetch_bluesky_search(query, gid)

            for item in fetched:
                if item["id"] in seen_ids:
                    continue
                seen_ids.add(item["id"])
                group_items.append(item)
                if len(group_items) >= max_per_group:
                    break

        if group_items:
            all_items.extend(group_items)
            used_groups.append(gid)
        else:
            skipped_groups.append(gid)

        if len(all_items) >= max_total:
            break

    return {
        "version": 1,
        "generated_at": _now_iso(),
        "note": "Raw intake. Temporary. Overwritten each run. Not for diary. Not for posting.",
        "stats": {
            "total": len(all_items),
            "curiosity_profile_available": bool(profile),
            "groups_used": used_groups,
            "groups_skipped": skipped_groups,
            "perplexity_available": has_perplexity,
        },
        "items": all_items,
    }


def _append_log(msg: str) -> None:
    try:
        with open(LOG_FILE, "a") as f:
            f.write(f"\n<!-- world_radar {_now_iso()} --> {msg}\n")
    except Exception:
        pass


def main() -> None:
    parser = argparse.ArgumentParser(description="Em World Radar — curiosity collector")
    parser.add_argument("--dry-run", action="store_true", help="Print instead of writing")
    parser.add_argument("--group", default=None, help="Run only one source group")
    args = parser.parse_args()

    sources = load_sources()
    if not sources:
        print("[world_radar] No sources loaded. Exiting.", file=sys.stderr)
        sys.exit(1)

    print(f"[world_radar] Starting collection. dry_run={args.dry_run}")
    inbox = collect(sources, only_group=args.group)

    stats = inbox["stats"]
    print(f"[world_radar] Collected {stats['total']} items from groups: {stats['groups_used']}")
    if stats.get("curiosity_profile_available"):
        print("[world_radar] Curiosity profile available — profile-driven queries included")
    if stats["groups_skipped"]:
        print(f"[world_radar] Skipped (no results): {stats['groups_skipped']}")
    if not stats["perplexity_available"]:
        print("[world_radar] PERPLEXITY_API_KEY not set — used Bluesky fallback only")

    if args.dry_run:
        print(json.dumps(inbox, indent=2, ensure_ascii=False))
        return

    INBOX_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(INBOX_FILE, "w") as f:
        json.dump(inbox, f, indent=2, ensure_ascii=False)
    print(f"[world_radar] Wrote {stats['total']} items to {INBOX_FILE}")

    _append_log(
        f"world_radar collected {stats['total']} items. "
        f"groups={stats['groups_used']} skipped={stats['groups_skipped']}"
    )


if __name__ == "__main__":
    main()
