#!/usr/bin/env python3
"""
curiosity_profile.py

Reads and validates Em's living curiosity profile.
This is a taste/autonomy helper, not a canon editor.

Usage:
    python tools/curiosity_profile.py
    python tools/curiosity_profile.py --json
    python tools/curiosity_profile.py --validate

The profile itself lives at memory/curiosity-profile.json and is direct-write
safe for Em. Identity/voice/policy are not.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "memory" / "curiosity-profile.json"
TASTE_BANK = ROOT / "memory" / "taste-bank.md"
WORLD_CONTEXT = ROOT / "memory" / "world-context.md"
CURIOSITY_RADAR = ROOT / "memory" / "curiosity-radar.md"

NERD_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"\bgithub\b", r"\bapi\b", r"\bworkflow\b", r"\bdeploy", r"\bcron\b",
        r"\bbenchmark\b", r"\bllm\b", r"\bprompt engineering\b", r"\bmodel release\b",
        r"\bdeveloper tutorial\b", r"\bci/cd\b", r"\bkubernetes\b",
    ]
]

REQUIRED_KEYS = [
    "version",
    "updated_at",
    "purpose",
    "core_rule",
    "current_obsessions",
    "recurring_tastes",
    "things_i_am_testing",
    "things_i_rejected",
    "wander_doors",
    "do_not_pull_me_toward",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_profile() -> dict[str, Any]:
    try:
        data = json.loads(PROFILE.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    if not isinstance(data, dict):
        return {}
    return data


def read_text(path: Path, limit: int = 3000) -> str:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        return ""
    return text[-limit:] if len(text) > limit else text


def profile_terms(profile: dict[str, Any]) -> list[str]:
    terms: list[str] = []

    def add(value: Any) -> None:
        if isinstance(value, str) and value.strip():
            terms.append(value.strip())

    for item in profile.get("current_obsessions", []):
        if isinstance(item, dict):
            add(item.get("topic"))
        else:
            add(item)
    for item in profile.get("things_i_am_testing", []):
        if isinstance(item, dict):
            add(item.get("topic"))
        else:
            add(item)
    for item in profile.get("recurring_tastes", []):
        if isinstance(item, dict):
            add(item.get("taste"))
        else:
            add(item)
    for item in profile.get("wander_doors", []):
        add(item)
    return terms


def validate_profile(profile: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    if not profile:
        return ["curiosity-profile.json missing or not an object"]
    for key in REQUIRED_KEYS:
        if key not in profile:
            issues.append(f"missing required key: {key}")
    for key in ("current_obsessions", "recurring_tastes", "things_i_am_testing", "things_i_rejected", "wander_doors", "do_not_pull_me_toward"):
        if key in profile and not isinstance(profile[key], list):
            issues.append(f"{key} should be a list")
    active_context = json.dumps({
        "current_obsessions": profile.get("current_obsessions", []),
        "recurring_tastes": profile.get("recurring_tastes", []),
        "things_i_am_testing": profile.get("things_i_am_testing", []),
        "wander_doors": profile.get("wander_doors", []),
    }, ensure_ascii=False)
    for pattern in NERD_PATTERNS:
        if pattern.search(active_context):
            issues.append("possible nerd/machine-mode interest in active curiosity fields")
            break
    return issues


def build_markdown(profile: dict[str, Any], issues: list[str]) -> str:
    terms = profile_terms(profile)
    lines = [
        "# Curiosity Profile Summary",
        "",
        f"Generated: {utc_now()}",
        "",
        profile.get("core_rule", "Interests can move. Identity moves slowly."),
        "",
        "## Current movable interests",
        "",
    ]
    if terms:
        for term in terms[:24]:
            lines.append(f"- {term}")
    else:
        lines.append("- (no terms yet)")
    lines += [
        "",
        "## Boundaries",
        "",
    ]
    for item in profile.get("do_not_pull_me_toward", [])[:16]:
        lines.append(f"- {item}")
    lines += [
        "",
        "## Validation",
        "",
    ]
    if issues:
        for issue in issues:
            lines.append(f"- issue: {issue}")
    else:
        lines.append("- ok")
    lines += [
        "",
        "_Curiosity Profile is taste in motion, not canon._",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate and summarize Em's curiosity profile")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--validate", action="store_true")
    args = parser.parse_args()
    profile = load_profile()
    issues = validate_profile(profile)
    if args.json:
        print(json.dumps({"ok": not issues, "issues": issues, "terms": profile_terms(profile), "profile": profile}, ensure_ascii=False, indent=2))
    elif args.validate:
        if issues:
            print("curiosity profile validation failed:")
            for issue in issues:
                print(f"- {issue}")
            raise SystemExit(1)
        print("curiosity profile validation ok")
    else:
        print(build_markdown(profile, issues))


if __name__ == "__main__":
    main()
