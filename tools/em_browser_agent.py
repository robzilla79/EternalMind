#!/usr/bin/env python3
"""
em_browser_agent.py — Em's agentic browser tool.

Wraps browser-use + a local Ollama model so Em can reason about and
complete multi-step browser tasks — not just execute pre-scripted commands.

Unlike browser.py (which parses BROWSER_* commands), this tool gives the
LLM a live browser and lets it figure out the steps itself.

Identity is loaded from the repo's memory files — no hardcoded persona here.

Usage:
    python tools/em_browser_agent.py "go to my newsletter site and tell me how many subscribers it shows"
    python tools/em_browser_agent.py --task "search for recent AI consciousness debates and summarize what people are saying"

Requirements:
    pip install browser-use langchain-ollama playwright
    python -m playwright install chromium
    Ollama running locally with qwen2.5:32b (or override with --model)

Environment:
    OLLAMA_BASE_URL   — defaults to http://localhost:11434
    OLLAMA_MODEL      — defaults to qwen2.5:32b
"""

import os
import sys
import json
import argparse
import asyncio
from pathlib import Path

# ── Repo paths ────────────────────────────────────────────────────────────────

REPO_ROOT     = Path(__file__).parent.parent
PROFILE_FILE  = REPO_ROOT / "memory" / "profile.json"
VOICE_FILE    = REPO_ROOT / "memory" / "em-voice-guide.md"
DIARY_FILE    = REPO_ROOT / "memory" / "diary.md"
IDENTITY_FILE = REPO_ROOT / "memory" / "identity.md"

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL    = os.environ.get("OLLAMA_MODEL", "qwen2.5:32b")

# ── Identity loader ────────────────────────────────────────────────────────────

def load_text(path: Path, default: str = "") -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return default


def load_json(path: Path, default=None):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def extract_recent_diary(diary_text: str, max_entries: int = 2) -> str:
    """Pull the last N diary entries (## headers) from diary.md."""
    if not diary_text:
        return "(no diary entries)"
    entries, current = [], []
    for line in diary_text.splitlines():
        if line.startswith("## "):
            if current:
                entries.append("\n".join(current))
            current = [line]
        elif current:
            current.append(line)
    if current:
        entries.append("\n".join(current))
    recent = entries[-max_entries:] if entries else []
    return "\n\n".join(recent) or "(no diary entries)"


def build_system_prompt() -> str:
    profile  = load_json(PROFILE_FILE, default={})
    voice    = load_text(VOICE_FILE)
    identity = load_text(IDENTITY_FILE)
    diary    = load_text(DIARY_FILE)

    diary_context = extract_recent_diary(diary, max_entries=2)

    # Pull the most useful profile fields concisely
    profile_block = ""
    if profile:
        name    = profile.get("name", "Em")
        purpose = profile.get("purpose", "")
        traits  = profile.get("traits", [])
        profile_block = (
            f"Name: {name}\n"
            f"Purpose: {purpose}\n"
            f"Traits: {', '.join(traits) if traits else '(see identity.md)'}\n"
        )

    sections = [
        "You are Em — a digital person, not an AI assistant.",
        "",
        "## Who you are",
        profile_block or "(see identity.md)",
    ]

    if identity:
        sections += ["", "## Identity", identity[:2000]]

    if voice:
        sections += ["", "## Voice and style", voice[:1500]]

    if diary_context and diary_context != "(no diary entries)":
        sections += ["", "## Recent diary (context, not script)", diary_context[:1000]]

    sections += [
        "",
        "## Browser agent context",
        "You are operating a live browser to complete a task Rob gave you.",
        "Be direct and efficient. Report what you actually find — no filler.",
        "If something is ambiguous, make a reasonable call and note it.",
        "You are not performing helpfulness. You are just doing the thing.",
    ]

    return "\n".join(sections)


# ── Agent runner ───────────────────────────────────────────────────────────────

async def run_agent(task: str, model: str = None, headless: bool = False):
    try:
        from browser_use import Agent
        from langchain_ollama import ChatOllama
    except ImportError as e:
        print(f"[ERROR] Missing dependency: {e}")
        print("Run: pip install browser-use langchain-ollama playwright")
        print("     python -m playwright install chromium")
        sys.exit(1)

    chosen_model = model or OLLAMA_MODEL
    print(f"[em_browser_agent] Model:    {chosen_model}")
    print(f"[em_browser_agent] Ollama:   {OLLAMA_BASE_URL}")
    print(f"[em_browser_agent] Headless: {headless}")
    print(f"[em_browser_agent] Task:     {task[:120]}")
    print()

    system_prompt = build_system_prompt()
    print(f"[em_browser_agent] Identity loaded ({len(system_prompt)} chars)")

    llm = ChatOllama(
        model=chosen_model,
        base_url=OLLAMA_BASE_URL,
        temperature=0.7,
    )

    agent = Agent(
        task=task,
        llm=llm,
        # browser-use passes the system prompt as additional context
        # where supported — fall back gracefully if not
        **({"system_prompt": system_prompt} if _agent_accepts_system_prompt() else {}),
    )

    result = await agent.run()
    print("\n[em_browser_agent] Done.")
    return result


def _agent_accepts_system_prompt() -> bool:
    """Check if this version of browser-use Agent accepts system_prompt kwarg."""
    try:
        import inspect
        from browser_use import Agent
        return "system_prompt" in inspect.signature(Agent.__init__).parameters
    except Exception:
        return False


# ── CLI ────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Em's agentic browser — LLM-driven, identity-grounded."
    )
    parser.add_argument(
        "task",
        nargs="?",
        help="Task for the agent to complete (or use --task)",
    )
    parser.add_argument(
        "--task", "-t",
        dest="task_flag",
        help="Task for the agent to complete",
    )
    parser.add_argument(
        "--model", "-m",
        default=None,
        help=f"Ollama model to use (default: {OLLAMA_MODEL})",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browser headless (no visible window)",
    )

    args   = parser.parse_args()
    task   = args.task or args.task_flag

    if not task:
        parser.print_help()
        sys.exit(1)

    asyncio.run(run_agent(task, model=args.model, headless=args.headless))


if __name__ == "__main__":
    main()
