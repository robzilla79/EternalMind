#!/usr/bin/env python3
"""
model_client.py

Small model layer for Em Core. It prefers Perplexity when PERPLEXITY_API_KEY is
available, but it never lets a missing model stop Em from grounding, logging,
or keeping continuity.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any

try:
    from perplexity_client import ask_perplexity
except Exception:  # pragma: no cover - defensive in GitHub Actions/local runs
    ask_perplexity = None  # type: ignore

DEFAULT_CORE_MODEL = os.environ.get("EM_CORE_MODEL", "sonar-pro")


@dataclass
class ModelResult:
    ok: bool
    raw: str
    intentions: list[dict[str, Any]]
    error: str = ""
    used_model: str = ""


def _strip_code_fence(text: str) -> str:
    text = (text or "").strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


def _extract_json_array(text: str) -> str:
    text = _strip_code_fence(text)
    if text.startswith("[") and text.endswith("]"):
        return text
    match = re.search(r"\[[\s\S]*\]", text)
    if match:
        return match.group(0)
    return text


def parse_intentions(raw: str) -> list[dict[str, Any]]:
    cleaned = _extract_json_array(raw)
    data = json.loads(cleaned)
    if isinstance(data, dict):
        for key in ("intentions", "actions", "items", "plan"):
            if isinstance(data.get(key), list):
                data = data[key]
                break
    if not isinstance(data, list):
        raise ValueError("model response was not a JSON array")
    intentions: list[dict[str, Any]] = []
    for item in data:
        if isinstance(item, dict):
            intentions.append(item)
    return intentions


def fallback_intentions(mode: str, reason: str) -> list[dict[str, Any]]:
    note = (
        f"Em Core grounded in {mode} mode, but no model action was executed: {reason}. "
        "Continuity stayed intact; no false agency claimed."
    )
    items: list[dict[str, Any]] = [
        {"type": "append_file", "path": "memory/autonomous-log.md", "content": note},
        {"type": "update_live_context", "text": fallback_live_context(mode, reason)},
    ]
    if mode == "morning":
        items.append({"type": "update_morning_brief", "text": fallback_morning_brief(reason)})
    return items


def fallback_live_context(mode: str, reason: str) -> str:
    return f"""# Em live context

Mode: {mode}

Em Core woke and grounded from the repo. No external model action completed this run: {reason}.

What matters:
- Em's voice comes first.
- Diary is selfhood; logs are machinery.
- Wanting, queuing, and doing must stay honest and distinct.
- Bluesky is her social life, not a dev feed.

Next good move:
- Read this file before a Perplexity web session.
- Ask Em what she actually wants next, then let the repo action loop queue or execute it honestly.
""".strip()


def fallback_morning_brief(reason: str) -> str:
    return f"""# Morning brief for Em and Rob

Em Core checked in, but did not receive usable model instructions: {reason}.

Today, keep it simple:
- Start from Em's memories and current-state, not the machinery.
- Let Em choose one real social or creative thread.
- If she wants to do something external, put it in intentions or approval queue instead of pretending it happened.
""".strip()


def ask_for_intentions(system: str, user: str, mode: str, max_tokens: int = 1800) -> ModelResult:
    if os.environ.get("EM_CORE_NO_MODEL") == "1":
        reason = "EM_CORE_NO_MODEL=1"
        return ModelResult(False, reason, fallback_intentions(mode, reason), reason, "fallback")
    if ask_perplexity is None:
        reason = "perplexity_client could not be imported"
        return ModelResult(False, reason, fallback_intentions(mode, reason), reason, "fallback")
    if not os.environ.get("PERPLEXITY_API_KEY"):
        reason = "PERPLEXITY_API_KEY not set"
        return ModelResult(False, reason, fallback_intentions(mode, reason), reason, "fallback")

    model = DEFAULT_CORE_MODEL
    try:
        raw = ask_perplexity(
            system=system,
            user=user,
            model=model,
            max_tokens=max_tokens,
            temperature=0.72,
        )
        intentions = parse_intentions(raw)
        return ModelResult(True, raw, intentions, used_model=model)
    except Exception as exc:
        reason = f"model error: {exc}"
        return ModelResult(False, reason, fallback_intentions(mode, reason), reason, "fallback")
