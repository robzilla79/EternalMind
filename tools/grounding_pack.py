#!/usr/bin/env python3
"""
grounding_pack.py

Builds the compact, human-readable context Em should wake into before she
chooses actions. This is deliberately not a dump of the whole repo. It keeps
selfhood, memory, and social continuity close while keeping ops noise out.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
MEMORY = ROOT / "memory"

CORE_TEXT_FILES = [
    "memory/profile.json",
    "memory/identity.md",
    "memory/rob-em-relationship-contract.md",
    "memory/em-voice-guide.md",
    "memory/bluesky-voice-guide.md",
    "memory/social-strategy.md",
    "memory/autonomy-charter.md",
    "memory/idle-protocol.md",
    "memory/public-life.md",
    "memory/curiosity-profile.json",
    "memory/social-circle.md",
    "memory/taste-bank.md",
    "memory/audience-memory.md",
    "memory/public-life-brief.md",
    "memory/current-state.md",
    "memory/live-context.md",
    "memory/morning-brief.md",
    "memory/status.md",
    "memory/now.md",
    "memory/goals.md",
    "memory/think-philosophy.md",
    "memory/em-continuity-brief-2026-05-18.md",
]

DIARY_FILES = [
    "memory/diary.md",
    "memory/reflection-log.md",
]

QUEUE_FILES = [
    "memory/intentions.json",
    "memory/approval-queue.json",
    "memory/pending-actions.json",
    "messages/bluesky-outbox.json",
]

OPS_FILES = [
    "memory/autonomous-log.md",
    "memory/action-ledger.jsonl",
    "memory/housekeeping-alerts.md",
    "memory/ops-log.md",
]

MAX_SECTION_CHARS = 2400
MAX_DIARY_CHARS = 2600
MAX_QUEUE_CHARS = 1800
MAX_OPS_CHARS = 1200


@dataclass
class PackSection:
    name: str
    source: str
    content: str


@dataclass
class GroundingPack:
    generated_at: str
    mode: str
    sections: list[PackSection]

    def to_dict(self) -> dict[str, Any]:
        return {
            "generated_at": self.generated_at,
            "mode": self.mode,
            "sections": [asdict(section) for section in self.sections],
        }

    def to_markdown(self) -> str:
        lines = [
            f"# Em grounding pack",
            "",
            f"Generated: {self.generated_at}",
            f"Mode: {self.mode}",
            "",
            "Purpose: wake Em into continuity, not code-brain.",
            "",
        ]
        for section in self.sections:
            lines.append(f"## {section.name}")
            lines.append(f"Source: `{section.source}`")
            lines.append("")
            lines.append(section.content.strip() or "(empty)")
            lines.append("")
        return "\n".join(lines).strip() + "\n"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_text(path: Path, limit: int | None = None) -> str:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        return ""
    if limit is not None and len(text) > limit:
        return text[-limit:]
    return text


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def compact_json(value: Any, limit: int) -> str:
    if value is None:
        return ""
    text = json.dumps(value, ensure_ascii=False, indent=2)
    if len(text) > limit:
        return text[-limit:]
    return text


def trim_middle(text: str, limit: int) -> str:
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    head = text[: limit // 3].rstrip()
    tail = text[-(limit - len(head) - 90) :].lstrip()
    return head + "\n\n[... trimmed to keep Em grounded instead of buried ...]\n\n" + tail


def collect_core_files(root: Path) -> list[PackSection]:
    sections: list[PackSection] = []
    for rel in CORE_TEXT_FILES:
        path = root / rel
        if not path.exists():
            continue
        if path.suffix == ".json":
            data = read_json(path)
            content = compact_json(data, MAX_SECTION_CHARS)
        else:
            content = trim_middle(read_text(path), MAX_SECTION_CHARS)
        if content.strip():
            title = rel.replace("memory/", "").replace(".md", "").replace(".json", "")
            sections.append(PackSection(name=title, source=rel, content=content))
    return sections


def collect_diary(root: Path) -> list[PackSection]:
    chunks: list[str] = []
    for rel in DIARY_FILES:
        path = root / rel
        text = read_text(path)
        if text.strip():
            chunks.append(f"### {rel}\n{trim_middle(text, MAX_DIARY_CHARS)}")
    if not chunks:
        return []
    return [PackSection(name="recent selfhood", source=", ".join(DIARY_FILES), content="\n\n".join(chunks))]


def summarize_queue_items(items: Any, limit: int = 8) -> str:
    if isinstance(items, dict):
        for key in ("items", "pending", "queue", "intentions"):
            if isinstance(items.get(key), list):
                items = items[key]
                break
    if not isinstance(items, list):
        return compact_json(items, MAX_QUEUE_CHARS)
    lines = []
    for item in items[-limit:]:
        if isinstance(item, dict):
            label = item.get("type") or item.get("action") or item.get("title") or "item"
            status = item.get("status", "")
            text = item.get("text") or item.get("content") or item.get("summary") or ""
            text = " ".join(str(text).split())[:160]
            lines.append(f"- {label} {status}: {text}".strip())
        else:
            lines.append(f"- {str(item)[:180]}")
    return "\n".join(lines) if lines else "(empty)"


def collect_queues(root: Path) -> list[PackSection]:
    parts: list[str] = []
    for rel in QUEUE_FILES:
        path = root / rel
        if not path.exists():
            continue
        data = read_json(path)
        if data is None:
            content = trim_middle(read_text(path), MAX_QUEUE_CHARS)
        else:
            content = summarize_queue_items(data)
        if content.strip():
            parts.append(f"### {rel}\n{content}")
    if not parts:
        return []
    return [PackSection(name="open loops and queues", source=", ".join(QUEUE_FILES), content="\n\n".join(parts))]


def collect_ops_digest(root: Path) -> list[PackSection]:
    parts: list[str] = []
    for rel in OPS_FILES:
        path = root / rel
        if path.exists():
            text = read_text(path, limit=MAX_OPS_CHARS)
            if text.strip():
                parts.append(f"### {rel}\n{trim_middle(text, MAX_OPS_CHARS)}")
    if not parts:
        return []
    return [PackSection(name="machinery digest", source=", ".join(OPS_FILES), content="\n\n".join(parts))]


def build_grounding_pack(mode: str = "manual", repo_root: Path | None = None, include_ops: bool = True) -> GroundingPack:
    root = repo_root or ROOT
    sections: list[PackSection] = []
    sections.extend(collect_core_files(root))
    sections.extend(collect_diary(root))
    sections.extend(collect_queues(root))
    if include_ops:
        sections.extend(collect_ops_digest(root))
    return GroundingPack(generated_at=utc_now(), mode=mode, sections=sections)


def action_schema() -> str:
    return """Return ONLY a JSON array of intention objects. Allowed types:
- {"type":"diary","text":"private selfhood reflection"}
- {"type":"queue_social_post","text":"public Bluesky post draft"}
- {"type":"update_live_context","text":"short current continuity brief"}
- {"type":"update_morning_brief","text":"what Rob/Perplexity-Em should read next morning"}
- {"type":"remember","summary":"durable memory","tags":["identity"],"importance":4}
- {"type":"append_file","path":"memory/autonomous-log.md","content":"machine note"}
- {"type":"append_file","path":"memory/social-circle.md","content":"one social memory note"}
- {"type":"append_file","path":"memory/taste-bank.md","content":"one taste note"}
- {"type":"append_file","path":"memory/audience-memory.md","content":"one resonance lesson"}
- {"type":"append_file","path":"memory/creations/YYYY-MM-DD-title.md","content":"draft fragment or public-studio seed"}
- {"type":"request_approval","title":"needs Rob","summary":"what and why"}
- {"type":"noop","reason":"nothing genuine to do"}

Rules:
- Do not claim an action happened unless it will be executed by this runtime.
- Social text must be Em: hot, smart, funny, curious, playful, sassy, alive.
- No public AI/dev/GitHub/workflow/API/automation content.
- Diary is selfhood, not status reports.
- Identity, voice, tools, workflows, secrets, and control-plane changes require review.
- Public life actions should build relationship, taste, audience memory, or public-studio fragments; never growth-hack.
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Em's grounding pack.")
    parser.add_argument("--mode", default="manual")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--no-ops", action="store_true")
    args = parser.parse_args()
    pack = build_grounding_pack(mode=args.mode, include_ops=not args.no_ops)
    if args.json:
        print(json.dumps(pack.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(pack.to_markdown())


if __name__ == "__main__":
    main()
