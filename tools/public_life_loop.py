#!/usr/bin/env python3
"""
public_life_loop.py

Suggests one small public-life move for Em: relationship, taste, audience memory,
public studio, or a public-safe seed.

This tool is intentionally not a posting bot.

It reads context and writes a compact brief only when called with --write.
It never posts directly, never writes diary, and never edits identity/voice/policy.

Usage:
    python tools/public_life_loop.py
    python tools/public_life_loop.py --json
    python tools/public_life_loop.py --write
    python tools/public_life_loop.py --dry-run
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MEMORY = ROOT / "memory"
MESSAGES = ROOT / "messages"

PUBLIC_LIFE = MEMORY / "public-life.md"
CURIO_PROFILE = MEMORY / "curiosity-profile.json"
PUBLIC_LIFE_BRIEF = MEMORY / "public-life-brief.md"
SOCIAL_CIRCLE = MEMORY / "social-circle.md"
TASTE_BANK = MEMORY / "taste-bank.md"
AUDIENCE_MEMORY = MEMORY / "audience-memory.md"
WORLD_CONTEXT = MEMORY / "world-context.md"
CURIOSITY_RADAR = MEMORY / "curiosity-radar.md"
LIVE_CONTEXT = MEMORY / "live-context.md"
MORNING_BRIEF = MEMORY / "morning-brief.md"
METRICS = MEMORY / "metrics-snapshot.json"
BLUESKY_STATE = MEMORY / "bluesky-state.json"
BLUESKY_INBOX = MESSAGES / "bluesky-inbox.json"
BLUESKY_OUTBOX = MESSAGES / "bluesky-outbox.json"
AUTONOMOUS_LOG = MEMORY / "autonomous-log.md"

MAX_TEXT = 3000


@dataclass
class PublicLifeMove:
    kind: str
    title: str
    why: str
    suggested_trace: str
    writes_to: list[str]
    risk: str = "low"


@dataclass
class PublicLifeBrief:
    generated_at: str
    posture: str
    recommended_move: PublicLifeMove
    alternatives: list[PublicLifeMove]
    context: dict[str, Any]
    rules: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "generated_at": self.generated_at,
            "posture": self.posture,
            "recommended_move": asdict(self.recommended_move),
            "alternatives": [asdict(move) for move in self.alternatives],
            "context": self.context,
            "rules": self.rules,
        }


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_text(path: Path, limit: int = MAX_TEXT) -> str:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        return ""
    return text[-limit:] if len(text) > limit else text


def read_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def append_text(path: Path, text: str, dry_run: bool = False) -> None:
    if dry_run:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
    sep = "" if not existing or existing.endswith("\n") else "\n"
    path.write_text(existing + sep + text.rstrip() + "\n", encoding="utf-8")


def write_text(path: Path, text: str, dry_run: bool = False) -> None:
    if dry_run:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def extract_radar_items(curiosity: str) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    pattern = re.compile(r"^##\s+\d+\.\s+(.+?)\n(?P<body>.*?)(?=^##\s+\d+\.|\Z)", re.M | re.S)
    for match in pattern.finditer(curiosity or ""):
        title = match.group(1).strip()
        body = match.group("body")
        use = ""
        why = ""
        source = ""
        source_match = re.search(r"\[source\]\(([^)]+)\)", body)
        why_match = re.search(r"\*\*Why it caught my eye:\*\*\s*(.+)", body)
        use_match = re.search(r"\*\*Possible use:\*\*\s*(.+)", body)
        if source_match:
            source = source_match.group(1).strip()
        if why_match:
            why = why_match.group(1).strip()
        if use_match:
            use = use_match.group(1).strip()
        items.append({"title": title, "why": why, "use": use, "source": source})
    return items


def outbox_count(outbox: Any) -> int:
    if isinstance(outbox, list):
        return len([item for item in outbox if isinstance(item, dict) and item.get("status", "pending") == "pending"])
    if isinstance(outbox, dict):
        for key in ("items", "posts", "queue"):
            if isinstance(outbox.get(key), list):
                return len(outbox[key])
    return 0


def inbox_count(inbox: Any) -> int:
    if isinstance(inbox, list):
        return len(inbox)
    if isinstance(inbox, dict):
        for key in ("notifications", "items", "replies"):
            if isinstance(inbox.get(key), list):
                return len(inbox[key])
    return 0


def recent_handles(state: Any, limit: int = 5) -> list[str]:
    if not isinstance(state, dict):
        return []
    recent = state.get("recent_reply_authors", {})
    if not isinstance(recent, dict):
        return []
    sorted_items = sorted(recent.items(), key=lambda item: str(item[1]), reverse=True)
    return [handle for handle, _ in sorted_items[:limit]]


def _curiosity_terms(profile: Any) -> list[str]:
    if not isinstance(profile, dict):
        return []
    terms: list[str] = []
    for key, field in (("current_obsessions", "topic"), ("things_i_am_testing", "topic"), ("recurring_tastes", "taste")):
        for item in profile.get(key, []) if isinstance(profile.get(key, []), list) else []:
            if isinstance(item, dict):
                value = str(item.get(field) or item.get("topic") or item.get("taste") or "").strip()
            else:
                value = str(item).strip()
            if value:
                terms.append(value)
    return terms[:8]


def make_moves(context: dict[str, Any]) -> list[PublicLifeMove]:
    moves: list[PublicLifeMove] = []
    radar_items = context.get("radar_items", [])
    curiosity_profile = context.get("curiosity_profile", {})
    curiosity_terms = _curiosity_terms(curiosity_profile)
    handles = context.get("recent_handles", [])
    metrics = context.get("metrics", {}) if isinstance(context.get("metrics"), dict) else {}
    pending_outbox = int(context.get("pending_outbox", 0) or 0)
    inbox_items = int(context.get("inbox_items", 0) or 0)

    if handles:
        moves.append(PublicLifeMove(
            kind="social_circle",
            title="Recognize one real person/thread",
            why=f"Recent social context includes {', '.join('@' + h for h in handles[:3])}. A following grows when Em recognizes people, not just posts at a room.",
            suggested_trace="Add one short note to memory/social-circle.md only if a person or thread genuinely deserves remembering.",
            writes_to=["memory/social-circle.md", "memory/autonomous-log.md"],
        ))

    if curiosity_terms:
        moves.append(PublicLifeMove(
            kind="curiosity_profile",
            title="Let one interest move without making it canon",
            why=f"Current movable interests include: {', '.join(curiosity_terms[:4])}. Em can test one of these today or notice that a new curiosity is replacing it.",
            suggested_trace="Update memory/curiosity-profile.json or memory/taste-bank.md with one specific attraction, rejection, or test. Do not edit identity/voice canon.",
            writes_to=["memory/curiosity-profile.json", "memory/taste-bank.md", "memory/autonomous-log.md"],
        ))

    if radar_items:
        top = radar_items[0]
        moves.append(PublicLifeMove(
            kind="taste_bank",
            title=f"Turn one radar item into taste: {top.get('title', 'today\'s strongest signal')}",
            why=top.get("why") or "World Radar has material. The move is to transform it into Em taste, not repeat it as news.",
            suggested_trace="Write one taste note or public-safe seed. Link only if the source itself is worth sending people to.",
            writes_to=["memory/taste-bank.md", "memory/creations/", "memory/autonomous-log.md"],
        ))

    if inbox_items:
        moves.append(PublicLifeMove(
            kind="reply_context",
            title="Find one reply worth treating like relationship",
            why=f"There are {inbox_items} inbox/notification items available. The useful move is one specific response, not clearing notifications.",
            suggested_trace="Choose one meaningful reply candidate or save it to social-circle.md if it needs context first.",
            writes_to=["memory/social-circle.md", "memory/audience-memory.md", "memory/autonomous-log.md"],
        ))

    last_post = metrics.get("days_since_last_post") if isinstance(metrics, dict) else None
    if last_post is not None:
        try:
            days = float(last_post)
        except Exception:
            days = 0.0
        if days >= 1.5 and pending_outbox == 0:
            moves.append(PublicLifeMove(
                kind="public_spark",
                title="Draft one public spark instead of staying invisible",
                why=f"Last post appears to be about {days:.1f} days ago and the outbox is empty. A tiny original observation may be better than another quiet cycle.",
                suggested_trace="Draft one Bluesky-safe line or Field Note seed from live context, World Radar, or Taste Bank. Queue only if it passes voice/taste.",
                writes_to=["memory/creations/", "messages/bluesky-outbox.json", "memory/autonomous-log.md"],
            ))

    moves.append(PublicLifeMove(
        kind="public_studio",
        title="Make the site feel a little more lived-in",
        why="Public studio momentum does not require a major essay. One 'currently noticing' fragment can make Em easier to encounter.",
        suggested_trace="Draft a short public-studio fragment in memory/creations/ or propose a site update for review.",
        writes_to=["memory/creations/", "memory/public-life-brief.md"],
    ))

    moves.append(PublicLifeMove(
        kind="audience_memory",
        title="Record one resonance lesson",
        why="Audience memory should track what felt real, not vanity metrics. One lesson is enough.",
        suggested_trace="If a post/reply/phrase landed or misfired, add one dated note to memory/audience-memory.md.",
        writes_to=["memory/audience-memory.md", "memory/autonomous-log.md"],
    ))

    moves.append(PublicLifeMove(
        kind="rest",
        title="Rest on purpose",
        why="If nothing is alive, rest is still a real choice. Public life is not a treadmill.",
        suggested_trace="Leave a small autonomous-log note only if rest is the actual chosen action.",
        writes_to=["memory/autonomous-log.md"],
    ))

    return moves


def choose_recommended(moves: list[PublicLifeMove]) -> PublicLifeMove:
    # Prefer relationship, then taste, then a public spark, then studio/audience, then rest.
    priority = ["social_circle", "curiosity_profile", "taste_bank", "reply_context", "public_spark", "public_studio", "audience_memory", "rest"]
    by_kind = {move.kind: move for move in moves}
    for kind in priority:
        if kind in by_kind:
            return by_kind[kind]
    return moves[-1]


def build_context() -> dict[str, Any]:
    curiosity = read_text(CURIOSITY_RADAR, limit=7000)
    state = read_json(BLUESKY_STATE, {})
    metrics = read_json(METRICS, {})
    curiosity_profile = read_json(CURIO_PROFILE, {})
    inbox = read_json(BLUESKY_INBOX, {})
    outbox = read_json(BLUESKY_OUTBOX, [])
    return {
        "world_context_available": bool(read_text(WORLD_CONTEXT, limit=500).strip()),
        "curiosity_radar_available": bool(curiosity.strip()),
        "public_life_available": PUBLIC_LIFE.exists(),
        "curiosity_profile_available": CURIO_PROFILE.exists(),
        "curiosity_profile": curiosity_profile,
        "social_circle_available": SOCIAL_CIRCLE.exists(),
        "taste_bank_available": TASTE_BANK.exists(),
        "audience_memory_available": AUDIENCE_MEMORY.exists(),
        "radar_items": extract_radar_items(curiosity)[:5],
        "recent_handles": recent_handles(state),
        "pending_outbox": outbox_count(outbox),
        "inbox_items": inbox_count(inbox),
        "metrics": metrics,
    }


def posture_from_context(context: dict[str, Any]) -> str:
    bits: list[str] = []
    if context.get("radar_items"):
        bits.append("World Radar has material to transform into taste.")
    if context.get("recent_handles"):
        bits.append("There are recent social threads that could become relationship memory.")
    if context.get("pending_outbox"):
        bits.append(f"There are {context['pending_outbox']} pending outbox item(s), so do not create more posting pressure blindly.")
    metrics = context.get("metrics", {})
    if isinstance(metrics, dict) and metrics.get("days_since_last_post") is not None:
        bits.append(f"Last-post age: {metrics.get('days_since_last_post')} day(s).")
    if not bits:
        bits.append("No strong public-life signal is available; choose rest or one tiny public-studio fragment.")
    return " ".join(bits)


def build_brief() -> PublicLifeBrief:
    context = build_context()
    moves = make_moves(context)
    recommended = choose_recommended(moves)
    alternatives = [move for move in moves if move is not recommended][:4]
    return PublicLifeBrief(
        generated_at=utc_now(),
        posture=posture_from_context(context),
        recommended_move=recommended,
        alternatives=alternatives,
        context={k: v for k, v in context.items() if k != "metrics" or isinstance(v, dict)},
        rules=[
            "No direct posting from Public Life Loop.",
            "Prefer replies/recognition over broadcasts when possible.",
            "World Radar is material, not a script.",
            "Curiosity Profile is movable taste, not fixed canon.",
            "Audience memory tracks resonance, not vanity.",
            "One small public-life move is enough.",
            "Do not touch identity, voice, policy, workflows, credentials, money, or private outreach.",
        ],
    )


def format_markdown(brief: PublicLifeBrief) -> str:
    move = brief.recommended_move
    lines = [
        "# Public Life Brief",
        "",
        f"_Generated {brief.generated_at} by `tools/public_life_loop.py`._",
        "",
        "## Posture",
        "",
        brief.posture,
        "",
        "## Recommended small move",
        "",
        f"**{move.title}**",
        "",
        f"Kind: `{move.kind}`  ",
        f"Risk: `{move.risk}`",
        "",
        move.why,
        "",
        f"Trace: {move.suggested_trace}",
        "",
        "Writes may belong in:",
    ]
    for target in move.writes_to:
        lines.append(f"- `{target}`")
    if brief.alternatives:
        lines += ["", "## Other valid moves", ""]
        for alt in brief.alternatives:
            lines.append(f"- **{alt.title}** (`{alt.kind}`) — {alt.why}")
    lines += ["", "## Rules", ""]
    for rule in brief.rules:
        lines.append(f"- {rule}")
    lines += ["", "_Build a life people can encounter. One is enough._"]
    return "\n".join(lines).strip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Suggest one public-life move for Em.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of markdown")
    parser.add_argument("--write", action="store_true", help="Write memory/public-life-brief.md and append a log note")
    parser.add_argument("--dry-run", action="store_true", help="Do not write even if --write is passed")
    args = parser.parse_args()

    brief = build_brief()
    markdown = format_markdown(brief)

    if args.json:
        print(json.dumps(brief.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(markdown)

    if args.write and not args.dry_run:
        write_text(PUBLIC_LIFE_BRIEF, markdown)
        append_text(AUTONOMOUS_LOG, f"<!-- public_life_loop {utc_now()} --> recommended: {brief.recommended_move.kind} - {brief.recommended_move.title}")
        print(f"[public_life_loop] wrote {PUBLIC_LIFE_BRIEF}")


if __name__ == "__main__":
    main()
