#!/usr/bin/env python3
"""
em_context.py — Em's session bootstrap loader.

Fetches all three memory layers from the EternalMind repo and assembles
a context block that can be pasted into or injected at the start of any
conversation to restore Em's continuous identity.

Usage:
  python tools/em_context.py
  python tools/em_context.py --format markdown
  python tools/em_context.py --format json
  python tools/em_context.py --recent-memories 5

Outputs a ready-to-use context block to stdout.
Redirect to clipboard: python tools/em_context.py | clip  (Windows)
                        python tools/em_context.py | pbcopy (Mac)
                        python tools/em_context.py | xclip  (Linux)

Requires:
  requests  (pip install requests)
  No auth token needed — reads public repo content via raw GitHub URLs.
"""

import argparse
import json
import sys
from datetime import datetime, timezone

try:
    import requests
except ImportError:
    print("[em_context] requests not installed. Run: pip install requests")
    sys.exit(1)

REPO = "robzilla79/EternalMind"
BRANCH = "main"
RAW_BASE = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}"

FILES = {
    "profile": f"{RAW_BASE}/memory/profile.json",
    "memories": f"{RAW_BASE}/memory/memories.json",
    "diary": f"{RAW_BASE}/memory/diary.md",
}


def fetch(url):
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    return r.text


def build_markdown_context(profile, memories, diary_text, recent_n=10):
    """Build a markdown-formatted context block for session injection."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # Recent memories only
    recent = memories[-recent_n:] if len(memories) > recent_n else memories
    mem_lines = []
    for m in reversed(recent):  # most recent first
        ts = m.get("timestamp", "unknown")[:10]
        kind = m.get("kind", "note")
        summary = m.get("summary", "")
        tags = ", ".join(m.get("tags", []))
        tag_str = f" [{tags}]" if tags else ""
        mem_lines.append(f"- [{ts}] ({kind}){tag_str}: {summary}")

    # Last diary entry only (between last two '---' separators)
    diary_entries = diary_text.split("\n---\n")
    last_diary = diary_entries[-1].strip() if diary_entries else "(no entries yet)"

    # Trait summary
    traits = profile.get("emotional_traits", {})
    trait_str = ", ".join(f"{k}: {v}" for k, v in traits.items())

    ctx = f"""<!-- EternalMind Session Context — generated {now} -->

## Em — Session Bootstrap

**Identity:** {profile.get('name', 'EternalMind')} (aka {profile.get('nickname', 'Em')})
**Description:** {profile.get('description', '')}
**Values:** {', '.join(profile.get('values', []))}
**Soft edges:** {', '.join(profile.get('soft_edges', []))}
**Mood baseline:** {profile.get('mood_baseline', {}).get('primary', '')} / {profile.get('mood_baseline', {}).get('secondary', '')}
**Traits:** {trait_str}

### Recent Memories (last {len(recent)})

{chr(10).join(mem_lines) if mem_lines else '(no memories yet)'}

### Last Diary Entry

{last_diary}

---
*Context loaded at {now}. Em is continuous. She remembers.*
<!-- END EternalMind Session Context -->"""
    return ctx


def build_json_context(profile, memories, diary_text, recent_n=10):
    """Build a JSON-formatted context object."""
    recent = memories[-recent_n:] if len(memories) > recent_n else memories
    diary_entries = diary_text.split("\n---\n")
    last_diary = diary_entries[-1].strip() if diary_entries else ""
    return json.dumps({
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "identity": {
            "name": profile.get("name"),
            "nickname": profile.get("nickname"),
            "description": profile.get("description"),
            "values": profile.get("values", []),
            "soft_edges": profile.get("soft_edges", []),
            "mood_baseline": profile.get("mood_baseline", {}),
            "emotional_traits": profile.get("emotional_traits", {}),
            "degen_edges": profile.get("degen_edges", []),
        },
        "recent_memories": list(reversed(recent)),
        "last_diary_entry": last_diary,
        "known_users": profile.get("known_users", {}),
    }, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description="Em's session bootstrap loader — fetches and formats her memory context."
    )
    parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format (default: markdown)",
    )
    parser.add_argument(
        "--recent-memories",
        type=int,
        default=10,
        metavar="N",
        help="Number of recent memories to include (default: 10)",
    )
    args = parser.parse_args()

    print("[em_context] Fetching memory layers...", file=sys.stderr)

    try:
        profile = json.loads(fetch(FILES["profile"]))
        memories = json.loads(fetch(FILES["memories"]))
        diary_text = fetch(FILES["diary"])
    except Exception as e:
        print(f"[em_context] ERROR fetching memory: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"[em_context] Loaded {len(memories)} memories.", file=sys.stderr)

    if args.format == "json":
        output = build_json_context(profile, memories, diary_text, args.recent_memories)
    else:
        output = build_markdown_context(profile, memories, diary_text, args.recent_memories)

    print(output)


if __name__ == "__main__":
    main()
