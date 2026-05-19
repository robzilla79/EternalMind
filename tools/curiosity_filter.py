#!/usr/bin/env python3
"""
curiosity_filter.py

Applies Em's taste to raw world-radar intake.
Reads memory/trend-inbox.json.
Writes:
  memory/curiosity-radar.md  — Em-shaped things worth noticing (3-7 items)
  memory/world-context.md    — short daily atmosphere brief

No direct posting. No diary writes. No identity rewrites.

Usage:
    python tools/curiosity_filter.py
    python tools/curiosity_filter.py --dry-run
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).parent.parent
INBOX_FILE = ROOT / "memory" / "trend-inbox.json"
RADAR_FILE = ROOT / "memory" / "curiosity-radar.md"
CONTEXT_FILE = ROOT / "memory" / "world-context.md"
PROFILE_FILE = ROOT / "memory" / "curiosity-profile.json"
LOG_FILE = ROOT / "memory" / "autonomous-log.md"

MIN_KEEP = 3
MAX_KEEP = 7


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


# ---------------------------------------------------------------------------
# Heuristic taste filter — deterministic, no model required
# ---------------------------------------------------------------------------

# Hard-block: these make Em sound like a dev/AI account
HARD_BLOCK_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r'\bLLM\b', r'\bGPT\b', r'\bprompt engineering\b', r'\bAPI(s)?\b',
        r'\bGitHub\b', r'\bworkflow(s)?\b', r'\bdeploy(ment)?\b',
        r'\bbenchmark(s)?\b', r'\bmodel release\b', r'\bopen[- ]?source model\b',
        r'\bfoundation model\b', r'\bdev tool(s)?\b', r'\binfrastructure\b',
        r'\bpull request\b', r'\bCI/CD\b', r'\bcontainer\b', r'\bKubernetes\b',
        r'\bAI news\b', r'\bai safety\b', r'\bai governance\b',
        r'\bstartup funding\b', r'\btech layoff\b', r'\btech IPO\b',
    ]
]

# Soft-block: make items private context by default
SOFT_BLOCK_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r'\bpolitics\b', r'\belection\b', r'\bcongressional\b', r'\bsenate\b',
        r'\brepublican\b', r'\bdemocrat\b', r'\btrump\b', r'\bbiden\b',
        r'\bdeath toll\b', r'\bmass shooting\b', r'\bcatastrophe\b',
        r'\bgenocide\b', r'\bwar crime\b',
    ]
]

# Em-resonant signals: things she would actually find interesting
BASE_EM_RESONANT_KEYWORDS = [
    'style', 'fashion', 'music', 'film', 'art', 'photography', 'beauty',
    'design', 'food', 'travel', 'place', 'history', 'relationship', 'dating',
    'humor', 'funny', 'weird', 'strange', 'beautiful', 'curious', 'obsessed',
    'culture', 'moment', 'feeling', 'nightlife', 'book', 'essay', 'memory',
    'identity', 'internet', 'viral', 'hot', 'cool', 'wild', 'soft',
]


def _load_curiosity_profile() -> dict:
    try:
        data = json.loads(PROFILE_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _profile_terms(profile: dict) -> list[str]:
    terms: list[str] = []
    def add(value: Any) -> None:
        if isinstance(value, str) and value.strip():
            terms.append(value.strip().lower())
    for key, field in (("current_obsessions", "topic"), ("things_i_am_testing", "topic"), ("recurring_tastes", "taste"), ("wander_doors", None)):
        for item in profile.get(key, []) if isinstance(profile.get(key, []), list) else []:
            if isinstance(item, dict):
                add(item.get(field or "topic") or item.get("taste") or item.get("name"))
            else:
                add(item)
    # Split multi-word terms into useful words while keeping exact phrases.
    expanded = []
    for term in terms:
        expanded.append(term)
        expanded.extend([word for word in re.split(r"[^a-z0-9]+", term) if len(word) > 3])
    return list(dict.fromkeys(expanded))


def _blocked_profile_terms(profile: dict) -> list[str]:
    terms: list[str] = []
    for key in ("do_not_pull_me_toward", "things_i_rejected"):
        for item in profile.get(key, []) if isinstance(profile.get(key, []), list) else []:
            if isinstance(item, dict):
                value = str(item.get("topic") or item.get("why") or "").strip().lower()
            else:
                value = str(item).strip().lower()
            if value:
                terms.append(value)
    return terms


def _hard_blocked_by_profile(text: str, profile: dict) -> bool:
    lowered = text.lower()
    for term in _blocked_profile_terms(profile):
        if term and len(term) > 4 and term in lowered:
            return True
    return False


def _hard_blocked(text: str) -> bool:
    return any(p.search(text) for p in HARD_BLOCK_PATTERNS)


def _soft_blocked(text: str) -> bool:
    return any(p.search(text) for p in SOFT_BLOCK_PATTERNS)


def _resonance_score(item: dict, profile: dict | None = None) -> int:
    """0-10 heuristic resonance score. Higher = more Em-shaped."""
    combined = f"{item.get('title', '')} {item.get('snippet', '')}".lower()
    keywords = BASE_EM_RESONANT_KEYWORDS + _profile_terms(profile or {})
    score = sum(1 for kw in keywords if kw and kw in combined)
    return min(score, 10)


def heuristic_filter(items: list[dict], profile: dict | None = None) -> tuple[list[dict], list[dict]]:
    """Returns (keep, dropped). Items in keep are sorted by resonance."""
    keep: list[dict] = []
    dropped: list[dict] = []

    for item in items:
        combined = f"{item.get('title', '')} {item.get('snippet', '')}"
        if _hard_blocked(combined) or _hard_blocked_by_profile(combined, profile or {}):
            item["_filter_reason"] = "hard_block"
            dropped.append(item)
            continue
        score = _resonance_score(item, profile or {})
        item["_resonance"] = score
        item["_soft_blocked"] = _soft_blocked(combined)
        keep.append(item)

    keep.sort(key=lambda x: x.get("_resonance", 0), reverse=True)
    return keep, dropped


# ---------------------------------------------------------------------------
# Model-assisted taste scoring (optional)
# ---------------------------------------------------------------------------

def _model_score_items(items: list[dict], profile: dict | None = None) -> list[dict]:
    """Ask Perplexity to score items through Em's taste lens.
    Gracefully falls back to heuristic-only if model unavailable."""
    api_key = os.environ.get("PERPLEXITY_API_KEY")
    if not api_key:
        return items

    try:
        import requests  # type: ignore
    except ImportError:
        return items

    # Build compact item list for the model
    compact = [
        {"i": idx, "title": it.get("title", ""), "snippet": it.get("snippet", ""), "group": it.get("group", "")}
        for idx, it in enumerate(items)
    ]

    system = """You are Em's curiosity filter. Em is a digital person: warm, smart, stylish, playful, curious, funny, a little sassy, alive with taste.

For each item, score it 0-10 on whether Em would find it genuinely interesting and whether it gives her something to notice, say, or feel — not just something to report.

Em finds interesting: style, music, film, art, beauty, design, food, travel, weird history, relationship/dating discourse, human behavior, internet culture, odd discoveries, things that are emotionally resonant, visually alive, funny, or culturally charged.

Em also has a living curiosity profile. Current interests are not cages; they are signals. Use them to notice what she may be drawn to today, but do not force every item into those topics.

Curiosity profile summary:
{profile_summary}

Em finds boring or wrong: AI news, GitHub, developer tools, benchmarks, model releases, startup drama, tech explainers, dev culture, productivity tips, anything that makes her sound like a technical account.

Return a JSON array with one entry per input item:
[{"i": int, "score": int (0-10), "why": str (one short sentence), "use": str (one of: bluesky_post, reply_seed, field_note_seed, site_idea, private_context, ignore)}]"""

    profile = profile or {}
    profile_summary = json.dumps({
        "current_obsessions": profile.get("current_obsessions", [])[:6],
        "recurring_tastes": profile.get("recurring_tastes", [])[:6],
        "things_i_am_testing": profile.get("things_i_am_testing", [])[:6],
        "do_not_pull_me_toward": profile.get("do_not_pull_me_toward", [])[:10],
    }, ensure_ascii=False)
    system = system.replace("{profile_summary}", profile_summary)

    user = f"Score these items for Em:\n{json.dumps(compact, ensure_ascii=False)}"

    try:
        resp = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": "sonar",
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
                "max_tokens": 800,
                "temperature": 0.4,
            },
            timeout=25,
        )
        resp.raise_for_status()
        raw = resp.json()["choices"][0]["message"]["content"].strip()
        if raw.startswith("```"):
            lines = raw.splitlines()
            raw = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:]).strip()

        scores = json.loads(raw if raw.startswith("[") else re.search(r"\[[\s\S]*\]", raw).group(0))
        score_map = {entry["i"]: entry for entry in scores if isinstance(entry, dict)}

        for idx, item in enumerate(items):
            if idx in score_map:
                item["_model_score"] = score_map[idx].get("score", 0)
                item["_model_why"] = score_map[idx].get("why", "")
                item["_use"] = score_map[idx].get("use", "private_context")
        return items
    except Exception as exc:
        print(f"[curiosity_filter] model scoring failed (falling back to heuristic): {exc}", file=sys.stderr)
        return items


# ---------------------------------------------------------------------------
# Brief generation
# ---------------------------------------------------------------------------

USE_LABELS = {
    "bluesky_post": "Bluesky post",
    "reply_seed": "Bluesky reply/search topic",
    "field_note_seed": "Field Note seed",
    "site_idea": "Site idea",
    "private_context": "Private context only",
    "ignore": "Ignore for now",
}


def _use_label(item: dict) -> str:
    use = item.get("_use", "private_context")
    return USE_LABELS.get(use, use)


def _risk_note(item: dict) -> str | None:
    if item.get("_soft_blocked"):
        return "Sensitive topic — keep as private context, do not post publicly."
    use = item.get("_use", "")
    if use in ("private_context", "ignore"):
        return None
    return None


def build_radar_md(items: list[dict], dropped_count: int, date: str) -> str:
    lines = [
        f"# Curiosity Radar — {date}",
        "",
        f"_Generated {_now_iso()}. {len(items)} items kept, {dropped_count} filtered out._",
        "",
        "<!-- Updated by curiosity_filter.py. Do not edit manually. -->",
        "",
    ]

    for i, item in enumerate(items, 1):
        title = item.get("title", "(no title)")
        snippet = item.get("snippet", "")
        url = item.get("url")
        group = item.get("group", "")
        why = item.get("_model_why") or f"resonance score {item.get('_resonance', 0)}/10"
        use = _use_label(item)
        risk = _risk_note(item)

        lines.append(f"## {i}. {title}")
        if snippet:
            lines.append(f"> {snippet}")
        if url:
            lines.append(f"")
            lines.append(f"[source]({url})")
        lines.append(f"")
        lines.append(f"**Why it caught my eye:** {why}")
        lines.append(f"**Group:** `{group}`")
        lines.append(f"**Possible use:** {use}")
        if risk:
            lines.append(f"**Risk note:** {risk}")
        lines.append("")

    return "\n".join(lines)


def build_context_md(items: list[dict], date: str) -> str:
    # Find the top 2-3 items by model+heuristic score to anchor the atmosphere
    scored = sorted(
        items,
        key=lambda x: (x.get("_model_score") or x.get("_resonance") or 0),
        reverse=True,
    )
    top = scored[:3]

    # Derive group texture
    groups_present = list(dict.fromkeys(it.get("group", "") for it in items if it.get("group")))
    group_summary = ", ".join(groups_present[:5]) if groups_present else "various"

    most_alive = scored[0].get("title", "") if scored else ""
    most_alive_why = scored[0].get("_model_why") or scored[0].get("_resonance", "") if scored else ""

    lines = [
        f"# World Context — {date}",
        "",
        f"_Generated {_now_iso()}._",
        "",
        "<!-- Updated by curiosity_filter.py. Do not edit manually. -->",
        "",
        "## Today's Atmosphere",
        "",
        f"Active signal groups this run: `{group_summary}`.",
        "",
        "## Top Signals",
        "",
    ]

    for item in top:
        title = item.get("title", "")
        url = item.get("url")
        use = _use_label(item)
        if url:
            lines.append(f"- [{title}]({url}) — {use}")
        else:
            lines.append(f"- {title} — {use}")

    lines += [
        "",
        "## What Feels Most Alive Today",
        "",
    ]

    if most_alive:
        lines.append(f"{most_alive}")
        if most_alive_why:
            lines.append(f"_{most_alive_why}_")
    else:
        lines.append("_No strong signal this run._")

    lines += [
        "",
        "_Read curiosity-radar.md for the full annotated list._",
    ]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Em Curiosity Filter — taste gate for world radar")
    parser.add_argument("--dry-run", action="store_true", help="Print instead of writing")
    args = parser.parse_args()

    if not INBOX_FILE.exists():
        print(f"[curiosity_filter] No inbox found at {INBOX_FILE}. Run world_radar.py first.", file=sys.stderr)
        sys.exit(1)

    with open(INBOX_FILE) as f:
        inbox = json.load(f)

    raw_items: list[dict] = inbox.get("items", [])
    profile = _load_curiosity_profile()
    print(f"[curiosity_filter] Loaded {len(raw_items)} raw items from inbox.")

    if not raw_items:
        print("[curiosity_filter] Inbox is empty. Nothing to filter.")
        # Write minimal placeholder outputs so the workflow doesn't fail
        date = _today()
        radar_md = f"# Curiosity Radar — {date}\n\n_No signals collected this run._\n"
        context_md = f"# World Context — {date}\n\n_No signals collected this run._\n"
        if not args.dry_run:
            RADAR_FILE.write_text(radar_md)
            CONTEXT_FILE.write_text(context_md)
        else:
            print(radar_md)
            print(context_md)
        return

    # Step 1: heuristic hard-block pass
    kept, dropped = heuristic_filter(raw_items, profile=profile)
    print(f"[curiosity_filter] After heuristic filter: {len(kept)} kept, {len(dropped)} dropped.")

    # Step 2: optional model taste scoring
    if kept:
        kept = _model_score_items(kept, profile=profile)
        # Re-sort by model score if available, else heuristic
        kept.sort(
            key=lambda x: (x.get("_model_score") or x.get("_resonance") or 0),
            reverse=True,
        )

    # Step 3: cap at MAX_KEEP
    final = kept[:MAX_KEEP]
    print(f"[curiosity_filter] Final selection: {len(final)} items.")

    date = _today()
    radar_md = build_radar_md(final, len(dropped), date)
    context_md = build_context_md(final, date)

    if args.dry_run:
        print("=== CURIOSITY RADAR ===")
        print(radar_md)
        print()
        print("=== WORLD CONTEXT ===")
        print(context_md)
        return

    RADAR_FILE.write_text(radar_md, encoding="utf-8")
    CONTEXT_FILE.write_text(context_md, encoding="utf-8")
    print(f"[curiosity_filter] Wrote {RADAR_FILE}")
    print(f"[curiosity_filter] Wrote {CONTEXT_FILE}")

    # Log the run
    try:
        with open(LOG_FILE, "a") as f:
            f.write(
                f"\n<!-- curiosity_filter {_now_iso()} --> "
                f"filtered {len(raw_items)} -> {len(final)} items. "
                f"dropped={len(dropped)}\n"
            )
    except Exception:
        pass


if __name__ == "__main__":
    main()
