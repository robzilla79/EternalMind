#!/usr/bin/env python3
"""
idle_planner.py

Reads Em's current context and suggests the most fitting idle action
from the Idle Menu in memory/idle-protocol.md.

This tool READS and SUGGESTS. It does not post, diary-write, or push
anything by default. Pass --write to allow it to append a suggestion
to memory/autonomous-log.md.

Usage:
    python tools/idle_planner.py              # suggest only, print to stdout
    python tools/idle_planner.py --write      # suggest + log to autonomous-log.md
    python tools/idle_planner.py --json       # output as JSON
    python tools/idle_planner.py --dry-run    # alias for default (no writes)

No direct posting. No diary writes. No identity changes.
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

# Files to read for context (all optional — graceful if missing)
CONTEXT_FILES = {
    "idle_protocol": ROOT / "memory" / "idle-protocol.md",
    "world_context": ROOT / "memory" / "world-context.md",
    "curiosity_radar": ROOT / "memory" / "curiosity-radar.md",
    "live_context": ROOT / "memory" / "live-context.md",
    "morning_brief": ROOT / "memory" / "morning-brief.md",
    "approval_queue": ROOT / "memory" / "approval-queue.json",
    "bluesky_inbox": ROOT / "messages" / "bluesky-inbox.json",
    "bluesky_outbox": ROOT / "messages" / "bluesky-outbox.json",
}

LOG_FILE = ROOT / "memory" / "autonomous-log.md"

IDLE_MENU = [
    {"id": 1, "name": "notice",   "label": "Notice one World Radar item and decide what it is for"},
    {"id": 2, "name": "search",   "label": "Search Bluesky for one real conversation worth joining"},
    {"id": 3, "name": "save",     "label": "Save one interesting person/account/artist to people.md"},
    {"id": 4, "name": "promote",  "label": "Promote one diary/world/social seed into a draft"},
    {"id": 5, "name": "draft",    "label": "Draft one small Field Note or public-studio fragment"},
    {"id": 6, "name": "garden",   "label": "Garden memory: promote, archive, or ignore recent material"},
    {"id": 7, "name": "taste",    "label": "Write one taste note about something beautiful, funny, strange, stylish, or emotionally sharp"},
    {"id": 8, "name": "prepare",  "label": "Prepare one thing to tell Rob next session"},
    {"id": 9, "name": "rest",     "label": "Rest, if nothing real pulls"},
]


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _read_optional(path: Path, limit: int = 2000) -> str:
    """Read a file if it exists; return empty string otherwise."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        return text[-limit:] if len(text) > limit else text
    except FileNotFoundError:
        return ""


def _read_json_optional(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _has_urgent_items(approval_queue: Any, bluesky_outbox: Any) -> bool:
    """Return True if there are items clearly waiting for Em's attention."""
    if isinstance(approval_queue, dict):
        items = approval_queue.get("items", [])
        if isinstance(items, list) and items:
            return True
    if isinstance(bluesky_outbox, dict):
        items = bluesky_outbox.get("posts", bluesky_outbox.get("items", []))
        if isinstance(items, list) and len(items) > 3:
            return True
    return False


def _has_fresh_radar(world_context: str, curiosity_radar: str) -> bool:
    """Return True if World Radar has recent content worth reviewing."""
    return bool(world_context.strip() and "No signals" not in world_context)


def _has_bluesky_inbox(bluesky_inbox: Any) -> bool:
    """Return True if there are unread inbox items."""
    if isinstance(bluesky_inbox, dict):
        items = bluesky_inbox.get("notifications", bluesky_inbox.get("items", []))
        return isinstance(items, list) and len(items) > 0
    return False


def suggest_idle_action(
    world_context: str,
    curiosity_radar: str,
    live_context: str,
    morning_brief: str,
    approval_queue: Any,
    bluesky_inbox: Any,
    bluesky_outbox: Any,
) -> dict:
    """
    Heuristic suggestion engine. Returns one idle action from the menu.
    Prefers rest when nothing genuinely pulls.
    """
    has_urgent = _has_urgent_items(approval_queue, bluesky_outbox)
    has_radar = _has_fresh_radar(world_context, curiosity_radar)
    has_inbox = _has_bluesky_inbox(bluesky_inbox)

    # If there are urgent items, signal that clearly — idle is not the right mode
    if has_urgent:
        return {
            "action": "noop",
            "menu_item": None,
            "reason": "Urgent items are waiting (approval queue or full outbox). Handle those first — idle is for the in-between, not the backlog.",
            "rest": False,
        }

    # Fresh radar: most natural idle starting point
    if has_radar:
        return {
            "action": "notice",
            "menu_item": IDLE_MENU[0],
            "reason": "World Radar has fresh signals. Pick one item, decide what it is for. That is enough.",
            "rest": False,
        }

    # Inbox has something: real conversation may be waiting
    if has_inbox:
        return {
            "action": "search",
            "menu_item": IDLE_MENU[1],
            "reason": "Bluesky inbox has items. Look for one real conversation worth joining, not just notifications to clear.",
            "rest": False,
        }

    # Morning brief present: maybe something there worth promoting into a draft
    if morning_brief.strip() and len(morning_brief) > 200:
        return {
            "action": "promote",
            "menu_item": IDLE_MENU[3],
            "reason": "Morning brief has content. See if one thread there wants to become a draft or taste note.",
            "rest": False,
        }

    # Default: rest. Nothing genuinely pulling.
    return {
        "action": "rest",
        "menu_item": IDLE_MENU[8],
        "reason": "Nothing genuinely pulls right now. Choosing rest on purpose rather than inventing motion. This is a complete, valid choice.",
        "rest": True,
    }


def build_output(suggestion: dict, context_availability: dict) -> dict:
    return {
        "generated_at": _now_iso(),
        "suggestion": suggestion,
        "context_available": context_availability,
        "rules": [
            "At most one idle action per Em Core run",
            "No direct posting",
            "No diary writes",
            "No identity/voice/workflow/policy changes",
            "Rest is valid",
            "No fake motion",
        ],
        "idle_menu": IDLE_MENU,
    }


def format_markdown(output: dict) -> str:
    s = output["suggestion"]
    action = s["action"]
    reason = s["reason"]
    menu_item = s.get("menu_item")
    ctx = output["context_available"]

    ctx_summary = ", ".join(k for k, v in ctx.items() if v) or "none"

    lines = [
        f"# Em Idle Planner — {output['generated_at']}",
        "",
        "## Suggestion",
        "",
        f"**Action:** `{action}`",
    ]
    if menu_item:
        lines.append(f"**Menu item {menu_item['id']}:** {menu_item['label']}")
    lines += [
        "",
        f"{reason}",
        "",
        "## Context available this run",
        "",
        f"`{ctx_summary}`",
        "",
        "## Rules reminder",
        "",
    ]
    for rule in output["rules"]:
        lines.append(f"- {rule}")
    lines += [
        "",
        "_Idle Protocol is a menu, not an assignment list. One is enough. Rest is valid._",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Em Idle Planner — suggests one idle action from the menu")
    parser.add_argument("--write", action="store_true", help="Append suggestion to autonomous-log.md")
    parser.add_argument("--dry-run", action="store_true", help="Read-only (same as default, explicit alias)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    # Load context
    world_context = _read_optional(CONTEXT_FILES["world_context"])
    curiosity_radar = _read_optional(CONTEXT_FILES["curiosity_radar"])
    live_context = _read_optional(CONTEXT_FILES["live_context"])
    morning_brief = _read_optional(CONTEXT_FILES["morning_brief"])
    approval_queue = _read_json_optional(CONTEXT_FILES["approval_queue"])
    bluesky_inbox = _read_json_optional(CONTEXT_FILES["bluesky_inbox"])
    bluesky_outbox = _read_json_optional(CONTEXT_FILES["bluesky_outbox"])

    context_availability = {
        "world_context": bool(world_context.strip()),
        "curiosity_radar": bool(curiosity_radar.strip()),
        "live_context": bool(live_context.strip()),
        "morning_brief": bool(morning_brief.strip()),
        "approval_queue": approval_queue is not None,
        "bluesky_inbox": bluesky_inbox is not None,
        "bluesky_outbox": bluesky_outbox is not None,
    }

    suggestion = suggest_idle_action(
        world_context=world_context,
        curiosity_radar=curiosity_radar,
        live_context=live_context,
        morning_brief=morning_brief,
        approval_queue=approval_queue,
        bluesky_inbox=bluesky_inbox,
        bluesky_outbox=bluesky_outbox,
    )

    output = build_output(suggestion, context_availability)

    if args.json:
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print(format_markdown(output))

    if args.write and not args.dry_run:
        try:
            action_label = suggestion["action"]
            reason = suggestion["reason"]
            log_line = f"\n<!-- idle_planner {_now_iso()} --> suggested: {action_label} — {reason[:120]}\n"
            with open(LOG_FILE, "a") as f:
                f.write(log_line)
            print(f"[idle_planner] Logged suggestion to {LOG_FILE}", flush=True)
        except Exception as exc:
            print(f"[idle_planner] Could not write log: {exc}")


if __name__ == "__main__":
    main()
