#!/usr/bin/env python3
"""
action_executor.py

Executes Em Core intentions through policy, voice, and agency-honesty gates.
The model proposes intentions; this executor decides whether they become real
repo changes, approval requests, or blocked ledger entries.
"""

from __future__ import annotations

import argparse
import json
import re
import hashlib
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

try:
    from repo_policy import DIRECT, PR_REQUIRED, BLOCKED, TIER_LABELS, allows_direct_write, validate, normalize_path
except Exception as exc:  # pragma: no cover
    raise RuntimeError(f"repo_policy is required for action execution: {exc}")

try:
    from voice_taste_gate import check_post
except Exception:  # pragma: no cover
    check_post = None  # type: ignore

ROOT = Path(__file__).resolve().parents[1]
LEDGER = "memory/action-ledger.jsonl"
APPROVAL_QUEUE = "memory/approval-queue.json"
INTENTIONS = "memory/intentions.json"
BLUESKY_OUTBOX = "messages/bluesky-outbox.json"
DIARY = "memory/diary.md"
AUTONOMOUS_LOG = "memory/autonomous-log.md"
LIVE_CONTEXT = "memory/live-context.md"
MORNING_BRIEF = "memory/morning-brief.md"
MEMORIES = "memory/memories.json"

OPS_DIARY_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"\bcron\b", r"\bworkflow\b", r"\bgithub\b", r"\bapi\b", r"\bdeploy\b",
        r"\bcommit\b", r"\bjson\b", r"\bstatus code\b", r"\bheartbeat\b",
        r"\bschedule slot\b", r"\bhousekeeping\b", r"\blog file\b", r"\btraceback\b",
        r"\bsecret\b", r"\btoken\b", r"\bvalidation passed\b", r"\bci\b",
    ]
]

MAX_TEXT_CHARS = 12000
MAX_SOCIAL_CHARS = 270
RECENT_SOCIAL_DEDUPE_LIMIT = 40


@dataclass
class ExecutionResult:
    ok: bool
    status: str
    action_type: str
    message: str
    path: str = ""
    id: str = ""
    tier: str = ""
    dry_run: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def event_id(prefix: str = "emcore") -> str:
    return f"{prefix}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"


def repo_path(path: str, root: Path = ROOT) -> Path:
    clean = normalize_path(path)
    return root / clean


def read_json_file(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def write_json_file(path: Path, data: Any, dry_run: bool = False) -> None:
    if dry_run:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def append_text_file(path: Path, text: str, dry_run: bool = False) -> None:
    if dry_run:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
    sep = "" if not existing or existing.endswith("\n") else "\n"
    path.write_text(existing + sep + text.rstrip() + "\n", encoding="utf-8")


def replace_text_file(path: Path, text: str, dry_run: bool = False) -> None:
    if dry_run:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def clean_text(value: Any, limit: int = MAX_TEXT_CHARS) -> str:
    text = str(value or "").strip()
    if len(text) > limit:
        text = text[:limit].rstrip() + "\n[trimmed]"
    return text


def looks_like_ops(text: str) -> bool:
    return any(pattern.search(text or "") for pattern in OPS_DIARY_PATTERNS)


def tier_label(tier: int) -> str:
    return TIER_LABELS.get(tier, str(tier))


def record_ledger(action: dict[str, Any], result: ExecutionResult, root: Path = ROOT, dry_run: bool = False) -> None:
    entry = {
        "timestamp": utc_now(),
        "action": action,
        "result": result.to_dict(),
    }
    append_text_file(repo_path(LEDGER, root), json.dumps(entry, ensure_ascii=False), dry_run=dry_run)


def add_approval_item(item: dict[str, Any], root: Path = ROOT, dry_run: bool = False) -> str:
    queue_path = repo_path(APPROVAL_QUEUE, root)
    data = read_json_file(queue_path, {"version": 1, "updated_at": None, "items": []})
    if isinstance(data, list):
        data = {"version": 1, "updated_at": None, "items": data}
    if not isinstance(data, dict):
        data = {"version": 1, "updated_at": None, "items": []}
    items = data.setdefault("items", [])
    item_id = item.get("id") or event_id("approval")
    item.update({"id": item_id, "queued_at": utc_now(), "status": item.get("status", "needs_rob")})
    items.append(item)
    data["updated_at"] = utc_now()
    write_json_file(queue_path, data, dry_run=dry_run)
    return item_id


def policy_write(path: str, content: str, mode: str, root: Path = ROOT, dry_run: bool = False) -> ExecutionResult:
    tier, violations = validate(path, content)
    label = tier_label(tier)
    if violations:
        return ExecutionResult(False, "blocked", mode, "; ".join(violations), path=path, tier=label, dry_run=dry_run)
    if tier == BLOCKED:
        return ExecutionResult(False, "blocked", mode, "blocked by repo policy", path=path, tier=label, dry_run=dry_run)
    if tier == PR_REQUIRED:
        approval_id = add_approval_item(
            {
                "title": f"Review requested for {path}",
                "summary": "Em Core proposed a write that requires Rob review.",
                "path": path,
                "mode": mode,
                "content": content,
                "tier": label,
            },
            root=root,
            dry_run=dry_run,
        )
        return ExecutionResult(False, "queued_for_review", mode, "write requires review", path=path, id=approval_id, tier=label, dry_run=dry_run)
    allowed, _, gate_violations = allows_direct_write(path, content)
    if not allowed:
        return ExecutionResult(False, "blocked", mode, "; ".join(gate_violations) or "direct write not allowed", path=path, tier=label, dry_run=dry_run)

    target = repo_path(path, root)
    if mode == "append_file":
        append_text_file(target, content, dry_run=dry_run)
    elif mode == "write_file":
        replace_text_file(target, content, dry_run=dry_run)
    else:
        return ExecutionResult(False, "blocked", mode, f"unknown write mode {mode}", path=path, tier=label, dry_run=dry_run)
    return ExecutionResult(True, "executed", mode, "direct write executed", path=path, tier=label, dry_run=dry_run)


def execute_diary(action: dict[str, Any], root: Path, dry_run: bool) -> ExecutionResult:
    text = clean_text(action.get("text") or action.get("content"), limit=4000)
    if not text:
        return ExecutionResult(False, "blocked", "diary", "empty diary text", dry_run=dry_run)
    stamp = utc_now()
    entry = f"\n---\n\n## {stamp} - Em Core\n\n{text}\n"
    if looks_like_ops(text):
        note = f"[{stamp}] Diary proposal reclassified as machinery log.\n\n{text}"
        result = policy_write(AUTONOMOUS_LOG, note, "append_file", root, dry_run)
        result.action_type = "diary_reclassified_to_log"
        return result
    return policy_write(DIARY, entry, "append_file", root, dry_run)


def execute_update_file(action: dict[str, Any], path: str, action_type: str, root: Path, dry_run: bool) -> ExecutionResult:
    text = clean_text(action.get("text") or action.get("content"), limit=8000)
    if not text:
        return ExecutionResult(False, "blocked", action_type, "empty content", path=path, dry_run=dry_run)
    if not text.lstrip().startswith("#"):
        title = "Em live context" if path == LIVE_CONTEXT else "Morning brief for Em and Rob"
        text = f"# {title}\n\n{text}"
    text = text.rstrip() + f"\n\n_Last updated by Em Core: {utc_now()}_\n"
    result = policy_write(path, text, "write_file", root, dry_run)
    result.action_type = action_type
    return result


def execute_remember(action: dict[str, Any], root: Path, dry_run: bool) -> ExecutionResult:
    summary = clean_text(action.get("summary") or action.get("text"), limit=1200)
    if not summary:
        return ExecutionResult(False, "blocked", "remember", "empty memory summary", dry_run=dry_run)
    importance = action.get("importance", 3)
    try:
        importance = int(importance)
    except Exception:
        importance = 3
    importance = max(1, min(5, importance))
    tags = action.get("tags", [])
    if not isinstance(tags, list):
        tags = [str(tags)]
    item = {
        "timestamp": utc_now(),
        "kind": action.get("kind", "em-core"),
        "summary": summary,
        "tags": [str(tag)[:40] for tag in tags[:8]],
        "importance": importance,
    }
    memories_path = repo_path(MEMORIES, root)
    data = read_json_file(memories_path, [])
    if not isinstance(data, list):
        return ExecutionResult(False, "blocked", "remember", "memories.json is not a list", path=MEMORIES, dry_run=dry_run)
    data.append(item)
    content = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    allowed, tier, violations = allows_direct_write(MEMORIES, content)
    if not allowed:
        return ExecutionResult(False, "blocked", "remember", "; ".join(violations) or "memory write blocked", path=MEMORIES, tier=tier_label(tier), dry_run=dry_run)
    write_json_file(memories_path, data, dry_run=dry_run)
    return ExecutionResult(True, "executed", "remember", "memory appended", path=MEMORIES, dry_run=dry_run)



def normalize_social_text(text: str) -> str:
    """Normalize public text for duplicate checks across punctuation/case variants."""
    text = (text or "").lower()
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"[“”\"'`’‘:;,.!?()\[\]{}\-—–_/\\]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def social_text_hash(text: str) -> str:
    return hashlib.sha256(normalize_social_text(text).encode("utf-8")).hexdigest()[:16]


def is_duplicate_social_text(outbox: Any, text: str) -> tuple[bool, str]:
    """Detect exact/near duplicate public text already queued or posted."""
    if not isinstance(outbox, list):
        return False, ""
    norm = normalize_social_text(text)
    if not norm:
        return False, ""
    new_words = set(norm.split())
    new_hash = social_text_hash(text)
    for item in outbox[-RECENT_SOCIAL_DEDUPE_LIMIT:]:
        if not isinstance(item, dict):
            continue
        existing_text = item.get("content") or item.get("text") or ""
        if not existing_text:
            continue
        existing_norm = normalize_social_text(existing_text)
        if not existing_norm:
            continue
        existing_hash = item.get("content_hash") or social_text_hash(existing_text)
        if existing_hash == new_hash or existing_norm == norm:
            return True, f"duplicate of {item.get('id') or item.get('uri') or 'recent outbox item'}"
        existing_words = set(existing_norm.split())
        if new_words and existing_words:
            overlap = len(new_words & existing_words) / max(1, min(len(new_words), len(existing_words)))
            if overlap >= 0.86 and abs(len(norm) - len(existing_norm)) <= 45:
                return True, f"near-duplicate of {item.get('id') or item.get('uri') or 'recent outbox item'}"
    return False, ""

def execute_social_post(action: dict[str, Any], root: Path, dry_run: bool) -> ExecutionResult:
    text = clean_text(action.get("text") or action.get("content"), limit=1000)
    if not text:
        return ExecutionResult(False, "blocked", "queue_social_post", "empty social text", dry_run=dry_run)
    if len(text) > MAX_SOCIAL_CHARS:
        return ExecutionResult(False, "blocked", "queue_social_post", f"social text too long ({len(text)} chars)", dry_run=dry_run)
    if check_post is None:
        return ExecutionResult(False, "blocked", "queue_social_post", "voice_taste_gate unavailable", dry_run=dry_run)
    gate = check_post(text)
    if not gate.get("ok"):
        reasons = "; ".join(gate.get("reasons", [])[:4])
        add_approval_item(
            {
                "title": "Social post blocked by taste gate",
                "summary": reasons,
                "proposed_text": text,
                "suggested_next": "Rewrite from feeling/taste, not mechanism.",
            },
            root=root,
            dry_run=dry_run,
        )
        return ExecutionResult(False, "blocked", "queue_social_post", reasons, path=BLUESKY_OUTBOX, dry_run=dry_run)

    outbox_path = repo_path(BLUESKY_OUTBOX, root)
    outbox = read_json_file(outbox_path, [])
    if not isinstance(outbox, list):
        return ExecutionResult(False, "blocked", "queue_social_post", "bluesky outbox is not a list", path=BLUESKY_OUTBOX, dry_run=dry_run)
    duplicate, duplicate_reason = is_duplicate_social_text(outbox, text)
    if duplicate:
        return ExecutionResult(False, "blocked", "queue_social_post", f"duplicate social post suppressed: {duplicate_reason}", path=BLUESKY_OUTBOX, dry_run=dry_run)
    post_id = action.get("id") or event_id("emcore-post")
    item = {
        "id": post_id,
        "type": "post",
        "content": text,
        "content_hash": social_text_hash(text),
        "queued_at": utc_now(),
        "source": "em_core",
        "status": "pending",
    }
    outbox.append(item)
    content = json.dumps(outbox, ensure_ascii=False, indent=2) + "\n"
    allowed, tier, violations = allows_direct_write(BLUESKY_OUTBOX, content)
    if not allowed:
        return ExecutionResult(False, "blocked", "queue_social_post", "; ".join(violations) or "outbox write blocked", path=BLUESKY_OUTBOX, tier=tier_label(tier), dry_run=dry_run)
    write_json_file(outbox_path, outbox, dry_run=dry_run)
    return ExecutionResult(True, "queued", "queue_social_post", "social post queued for Bluesky sync", path=BLUESKY_OUTBOX, id=post_id, dry_run=dry_run)


def execute_request_approval(action: dict[str, Any], root: Path, dry_run: bool) -> ExecutionResult:
    title = clean_text(action.get("title") or "Em Core approval request", limit=160)
    summary = clean_text(action.get("summary") or action.get("reason") or action.get("text"), limit=3000)
    approval_id = add_approval_item(
        {
            "title": title,
            "summary": summary,
            "source_action": action,
        },
        root=root,
        dry_run=dry_run,
    )
    return ExecutionResult(True, "queued_for_rob", "request_approval", "approval request queued", path=APPROVAL_QUEUE, id=approval_id, dry_run=dry_run)


def execute_intention(action: dict[str, Any], root: Path = ROOT, dry_run: bool = False) -> ExecutionResult:
    if not isinstance(action, dict):
        return ExecutionResult(False, "blocked", "unknown", "action was not an object", dry_run=dry_run)
    action_type = str(action.get("type") or action.get("action") or "noop").strip().lower()

    if action_type == "noop":
        return ExecutionResult(True, "noop", "noop", clean_text(action.get("reason") or "no action chosen", limit=400), dry_run=dry_run)
    if action_type == "diary":
        return execute_diary(action, root, dry_run)
    if action_type == "append_file":
        path = clean_text(action.get("path"), limit=500)
        content = clean_text(action.get("content") or action.get("text"))
        return policy_write(path, content, "append_file", root, dry_run)
    if action_type in ("write_file", "replace_file"):
        path = clean_text(action.get("path"), limit=500)
        content = clean_text(action.get("content") or action.get("text"))
        return policy_write(path, content, "write_file", root, dry_run)
    if action_type == "update_live_context":
        return execute_update_file(action, LIVE_CONTEXT, action_type, root, dry_run)
    if action_type == "update_morning_brief":
        return execute_update_file(action, MORNING_BRIEF, action_type, root, dry_run)
    if action_type == "remember":
        return execute_remember(action, root, dry_run)
    if action_type in ("queue_social_post", "social_post", "post"):
        return execute_social_post(action, root, dry_run)
    if action_type in ("request_approval", "external_action", "needs_rob"):
        return execute_request_approval(action, root, dry_run)

    approval_id = add_approval_item(
        {
            "title": f"Unknown Em Core action: {action_type}",
            "summary": "The model proposed an action type the executor does not know how to perform.",
            "source_action": action,
        },
        root=root,
        dry_run=dry_run,
    )
    return ExecutionResult(False, "queued_for_review", action_type, "unknown action type", path=APPROVAL_QUEUE, id=approval_id, dry_run=dry_run)


def execute_intentions(actions: Iterable[dict[str, Any]], root: Path = ROOT, dry_run: bool = False) -> list[ExecutionResult]:
    results: list[ExecutionResult] = []
    for action in actions:
        result = execute_intention(action, root=root, dry_run=dry_run)
        record_ledger(action, result, root=root, dry_run=dry_run)
        results.append(result)
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Execute Em Core intentions from a JSON file or stdin.")
    parser.add_argument("json_file", nargs="?")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.json_file:
        raw = Path(args.json_file).read_text(encoding="utf-8")
    else:
        import sys
        raw = sys.stdin.read()
    data = json.loads(raw)
    if isinstance(data, dict):
        data = data.get("intentions") or data.get("actions") or []
    if not isinstance(data, list):
        raise SystemExit("input must be a JSON array or object with intentions/actions")
    results = execute_intentions(data, dry_run=args.dry_run)
    print(json.dumps([result.to_dict() for result in results], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
