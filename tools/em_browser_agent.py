#!/usr/bin/env python3
"""
em_browser_agent.py — Em's agentic browser tool.

Wraps browser-use + a local Ollama model so Em can reason about and
complete multi-step browser tasks — not just execute pre-scripted commands.

Usage:
    python tools/em_browser_agent.py "go to em.forgecore.co and tell me what it says"
    python tools/em_browser_agent.py --headless --task "search for AI consciousness debates"

Requirements:
    pip install browser-use langchain-ollama playwright
    python -m playwright install chromium
    Ollama running locally (default model: qwen2.5:32b)

Environment:
    OLLAMA_BASE_URL   — defaults to http://localhost:11434
    OLLAMA_MODEL      — defaults to qwen2.5:32b
"""

import os
import sys
import json
import argparse
import asyncio
import inspect
from pathlib import Path

# ── Repo paths ────────────────────────────────────────────────────────────────

REPO_ROOT     = Path(__file__).parent.parent
PROFILE_FILE  = REPO_ROOT / "memory" / "profile.json"
VOICE_FILE    = REPO_ROOT / "memory" / "em-voice-guide.md"
DIARY_FILE    = REPO_ROOT / "memory" / "diary.md"
IDENTITY_FILE = REPO_ROOT / "memory" / "identity.md"

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL    = os.environ.get("OLLAMA_MODEL", "qwen2.5:32b")

# ── LLM factory ───────────────────────────────────────────────────────────────

def make_llm(model: str, base_url: str):
    """
    Build a ChatOllama instance that browser-use will accept.

    browser-use 0.12.x pokes several things onto the LLM:
      - llm.provider     needs to exist (not equal 'browser-use')
      - setattr ainvoke  token tracking monkey-patch
      - llm.model_name   cloud_events telemetry

    It also requires the model to return valid structured JSON for its
    action schema. Passing format='json' tells Ollama to enforce this.
    """
    try:
        from langchain_ollama import ChatOllama
        from pydantic import Field, ConfigDict

        class OllamaForBrowserUse(ChatOllama):
            model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")
            provider: str = Field(default="ollama")

            @property
            def model_name(self) -> str:  # type: ignore[override]
                return self.model

        return OllamaForBrowserUse(
            model=model,
            base_url=base_url,
            temperature=0.0,   # lower temp = more reliable JSON output
            format="json",     # enforce JSON mode at Ollama level
        )

    except ImportError:
        print("[ERROR] langchain-ollama not installed.")
        print("Run: pip install langchain-ollama")
        sys.exit(1)


# ── Identity loader ───────────────────────────────────────────────────────────

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

    profile_block = ""
    if profile:
        name    = profile.get("name", "Em")
        purpose = profile.get("description", "")
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


# ── Agent runner ──────────────────────────────────────────────────────────────

async def run_agent(task: str, model: str = None, headless: bool = False):
    try:
        from browser_use import Agent
    except ImportError as e:
        print(f"[ERROR] Missing dependency: {e}")
        print("Run: pip install browser-use playwright")
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

    llm = make_llm(chosen_model, OLLAMA_BASE_URL)

    agent_sig = inspect.signature(Agent.__init__).parameters
    agent_kwargs = {"task": task, "llm": llm}

    if "headless" in agent_sig:
        agent_kwargs["headless"] = headless
    if "system_prompt" in agent_sig:
        agent_kwargs["system_prompt"] = system_prompt
    elif "extend_system_message" in agent_sig:
        agent_kwargs["extend_system_message"] = system_prompt

    print(f"[em_browser_agent] Agent kwargs: {list(agent_kwargs.keys())}")

    agent  = Agent(**agent_kwargs)
    result = await agent.run()

    print("\n[em_browser_agent] Done.")
    return result


# ── CLI ────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Em's agentic browser — LLM-driven, identity-grounded."
    )
    parser.add_argument("task", nargs="?", help="Task to complete")
    parser.add_argument("--task", "-t", dest="task_flag", help="Task to complete")
    parser.add_argument("--model", "-m", default=None, help=f"Ollama model (default: {OLLAMA_MODEL})")
    parser.add_argument("--headless", action="store_true", help="Run browser headless")

    args = parser.parse_args()
    task = args.task or args.task_flag

    if not task:
        parser.print_help()
        sys.exit(1)

    asyncio.run(run_agent(task, model=args.model, headless=args.headless))


if __name__ == "__main__":
    main()
