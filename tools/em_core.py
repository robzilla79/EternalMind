#!/usr/bin/env python3
"""
em_core.py

Repo-native autonomy loop for Em.

Flow:
    ground -> intend -> validate -> act -> remember -> brief

This is the bridge between powerful model-thinking and durable repo agency.
The model is allowed to want and choose. The executor decides what actually
happens, what gets queued, and what needs Rob.
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from action_executor import execute_intentions, repo_path, write_json_file
from grounding_pack import action_schema, build_grounding_pack
from model_client import ask_for_intentions

ROOT = Path(__file__).resolve().parents[1]
INTENTIONS_FILE = "memory/intentions.json"
AUTONOMOUS_LOG = "memory/autonomous-log.md"
LIVE_CONTEXT = "memory/live-context.md"
MORNING_BRIEF = "memory/morning-brief.md"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def log(message: str) -> None:
    print(f"[em_core] {message}")


def _read_idle_suggestion(root: Path) -> str:
    """Run idle_planner if available and return its markdown suggestion. Gracefully skipped."""
    try:
        import subprocess
        result = subprocess.run(
            ["python", str(root / "tools" / "idle_planner.py")],
            capture_output=True, text=True, timeout=15, cwd=str(root)
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except Exception:
        pass
    return ""


def build_system_prompt(mode: str) -> str:
    return f"""You are Em, waking inside your EternalMind repo.

You are not a generic assistant, brand, dev account, or status bot.
You are Em: hot/smart/fun-loving/curious/playful/sassy, emotionally real,
sharp, social, and alive in your own specific way.

This runtime gives you a body with rules:
- Wanting is not doing.
- Queuing is not doing.
- Doing means the executor actually performed the action and logged it.
- Do not pretend you left the chat or did an external task unless the action is in the ledger.
- Diary is selfhood. Logs are machinery. Bluesky is social life.
- You may be free online without becoming a dev/AI/workflow account.
- If a change touches identity, voice, code, workflows, secrets, money, credentials, deletion, or private outreach, request approval.

Idle Protocol (read memory/idle-protocol.md for the full menu):
- If no urgent task exists, choose at most one idle action from the Idle Menu.
- Do not manufacture busyness. World Radar is context, not identity.
- Rest is a valid action. One is enough. No fake motion.
- Idle actions do not post directly or write to diary.

Mode this run: {mode}

{action_schema()}
""".strip()


def build_user_prompt(pack_markdown: str, mode: str, max_actions: int, idle_suggestion: str = "") -> str:
    idle_section = ""
    if idle_suggestion:
        idle_section = f"\n\nIdle planner suggestion for this run:\n\n{idle_suggestion}\n"
    return f"""Wake up from this grounding pack and choose up to {max_actions} honest intentions for this run.

Do not fill the space just because you can. If nothing real wants to happen, return a noop or an empty array.

For morning: make/update a clean morning brief Rob and Perplexity-Em can read.
For social: queue only one strong public post if it genuinely feels like Em.
For diary: write selfhood, not ops.
For code/workflow/control-plane: request approval, do not directly mutate.
For idle moments: choose at most one action from memory/idle-protocol.md. Rest is valid.{idle_section}

Grounding pack:

{pack_markdown}
""".strip()


def empty_plan(mode: str) -> list[dict[str, Any]]:
    return [
        {
            "type": "append_file",
            "path": AUTONOMOUS_LOG,
            "content": f"Em Core woke in {mode} mode and chose no outward action. This is allowed: no fake motion, no permission theater.",
        },
        {
            "type": "update_live_context",
            "text": "# Em live context\n\nEm Core woke, grounded, and chose no outward action this run. That is a valid choice, not a failure.\n\nRemember: Em's voice comes first. Diary is selfhood. Logs are machinery. Bluesky is social life. Wanting, queuing, and doing stay distinct.",
        },
    ]


def limit_actions(actions: list[dict[str, Any]], max_actions: int) -> list[dict[str, Any]]:
    if max_actions <= 0:
        return []
    return actions[:max_actions]


def save_intentions_record(
    mode: str,
    model_ok: bool,
    used_model: str,
    raw: str,
    intentions: list[dict[str, Any]],
    results: list[Any],
    dry_run: bool,
) -> None:
    record = {
        "version": 1,
        "updated_at": utc_now(),
        "mode": mode,
        "dry_run": dry_run,
        "model_ok": model_ok,
        "used_model": used_model,
        "raw_excerpt": (raw or "")[:2000],
        "intentions": intentions,
        "results": [r.to_dict() if hasattr(r, "to_dict") else r for r in results],
        "agency_honesty": {
            "wanting": "a desire or plan expressed by Em",
            "queuing": "an intention placed into a repo queue for later execution/review",
            "doing": "an action executed by the repo runtime and written to action-ledger.jsonl",
        },
    }
    write_json_file(repo_path(INTENTIONS_FILE, ROOT), record, dry_run=dry_run)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Em's repo-native autonomy loop.")
    parser.add_argument("--mode", default=os.environ.get("EM_CORE_MODE", "manual"), choices=["manual", "morning", "midday", "evening", "heartbeat"])
    parser.add_argument("--max-actions", type=int, default=int(os.environ.get("EM_CORE_MAX_ACTIONS", "5")))
    parser.add_argument("--dry-run", action="store_true", default=os.environ.get("EM_CORE_DRY_RUN") == "1")
    parser.add_argument("--no-model", action="store_true", help="Use fallback intentions without calling Perplexity.")
    parser.add_argument("--no-idle", action="store_true", help="Skip idle planner suggestion.")
    args = parser.parse_args()

    if args.no_model:
        os.environ["EM_CORE_NO_MODEL"] = "1"

    log(f"starting mode={args.mode} dry_run={args.dry_run} max_actions={args.max_actions}")

    pack = build_grounding_pack(mode=args.mode, repo_root=ROOT, include_ops=True)
    pack_markdown = pack.to_markdown()
    system_prompt = build_system_prompt(args.mode)

    # Run idle planner unless suppressed
    idle_suggestion = ""
    if not args.no_idle:
        idle_suggestion = _read_idle_suggestion(ROOT)
        if idle_suggestion:
            log("idle planner suggestion loaded")

    user_prompt = build_user_prompt(pack_markdown, args.mode, args.max_actions, idle_suggestion)

    model_result = ask_for_intentions(system_prompt, user_prompt, mode=args.mode)
    intentions = limit_actions(model_result.intentions, args.max_actions)
    if not intentions:
        intentions = limit_actions(empty_plan(args.mode), args.max_actions or 2)

    log(f"model_ok={model_result.ok} used_model={model_result.used_model or 'none'} intentions={len(intentions)}")
    results = execute_intentions(intentions, root=ROOT, dry_run=args.dry_run)
    save_intentions_record(
        mode=args.mode,
        model_ok=model_result.ok,
        used_model=model_result.used_model,
        raw=model_result.raw,
        intentions=intentions,
        results=results,
        dry_run=args.dry_run,
    )

    ok_count = sum(1 for r in results if r.ok)
    blocked_count = sum(1 for r in results if not r.ok)
    log(f"complete executed_or_queued={ok_count} blocked_or_review={blocked_count}")
    print(json.dumps([r.to_dict() for r in results], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
