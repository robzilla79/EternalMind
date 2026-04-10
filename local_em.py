import ollama
import json
import datetime
import subprocess
import os
import re
from datetime import timezone

# ── CONFIG ────────────────────────────────────────────────────────────────────────────
os.environ.setdefault("OLLAMA_HOST", "http://127.0.0.1:11434")

# Load .env file if present
_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if os.path.exists(_env_path):
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            # Skip blank lines, comments, and lines without =
            if not _line or _line.startswith("#") or "=" not in _line:
                continue
            _k, _v = _line.split("=", 1)
            _k = _k.strip()
            _v = _v.strip()
            # Only set valid env var names (letters, digits, underscores, must not start with digit)
            if re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', _k):
                os.environ.setdefault(_k, _v)

MODEL             = "qwen2.5:32b"
EM_DIR            = os.path.dirname(os.path.abspath(__file__))
MEM_DIR           = os.path.join(EM_DIR, "memory")
TASKS_PATH        = os.path.join(EM_DIR, "tasks.md")
LAST_THOUGHT_PATH = os.path.join(EM_DIR, ".last_thought")
CURIOSITY_COOLDOWN_MINUTES = 30
TASK_DIVIDER = "*(Replace everything below this line with your task when you have one)*"

# ── TOOL EXECUTOR ───────────────────────────────────────────────────────────────────────
def execute_tools(response_text: str) -> str:
    tool_pattern = re.compile(r'TOOL:\s*web_search\(["\'](.+?)["\']\)', re.IGNORECASE)
    matches = tool_pattern.findall(response_text)
    if not matches:
        return ""
    from tools.web_search import search
    results = []
    for query in matches:
        print(f"  🔍 Em is searching: {query}")
        result = search(query)
        results.append(f"--- Search results for: {query} ---\n{result}")
    return "\n\n".join(results)

def extract_notify(response_text: str) -> str | None:
    """Check if Em wants to notify Rob. Syntax: NOTIFY: message here"""
    match = re.search(r'NOTIFY:\s*(.+)', response_text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None

# ── TASK HELPERS ───────────────────────────────────────────────────────────────────────
def _extract_task_content(raw: str) -> str:
    if TASK_DIVIDER in raw:
        after = raw.split(TASK_DIVIDER, 1)[1].strip()
        return after
    return raw.strip()

def has_task() -> bool:
    if os.path.exists(TASKS_PATH):
        with open(TASKS_PATH, "r", encoding="utf-8") as f:
            raw = f.read()
        task = _extract_task_content(raw)
        if len(task) >= 10 and "**status: done**" not in task.lower():
            return True
    return False

# ── COOLDOWN CHECK ──────────────────────────────────────────────────────────────────────────────
def curiosity_cooled_down() -> bool:
    if not os.path.exists(LAST_THOUGHT_PATH):
        return True
    with open(LAST_THOUGHT_PATH, "r") as f:
        last = f.read().strip()
    try:
        last_time = datetime.datetime.fromisoformat(last)
        elapsed = (datetime.datetime.now(timezone.utc) - last_time).total_seconds() / 60
        return elapsed >= CURIOSITY_COOLDOWN_MINUTES
    except Exception:
        return True

def mark_thought_time():
    with open(LAST_THOUGHT_PATH, "w") as f:
        f.write(datetime.datetime.now(timezone.utc).isoformat())

# ── LOAD SOUL ──────────────────────────────────────────────────────────────────────────────
def load_bootstrap() -> str:
    with open(os.path.join(MEM_DIR, "bootstrap.md"), "r", encoding="utf-8") as f:
        return f.read()

def load_recent_context() -> str:
    """Load last 3 diary entries so Em remembers what she was just thinking about."""
    diary_path = os.path.join(MEM_DIR, "diary.md")
    if not os.path.exists(diary_path):
        return ""
    with open(diary_path, "r", encoding="utf-8") as f:
        content = f.read()
    entries = re.split(r'(?=###\s+\d{4}-\d{2}-\d{2})', content)
    recent = entries[-3:] if len(entries) >= 3 else entries
    return "\n".join(recent).strip()

# ── GET TASK ───────────────────────────────────────────────────────────────────────────────
def get_task() -> str:
    if os.path.exists(TASKS_PATH):
        with open(TASKS_PATH, "r", encoding="utf-8") as f:
            raw = f.read()
        task = _extract_task_content(raw)
        if len(task) >= 10 and "**status: done**" not in task.lower():
            return (
                f"Task from Rob:\n\n{task}\n\n"
                "---\n"
                "When you finish (or make meaningful progress), update tasks.md yourself:\n"
                "- If fully done: append '\\n\\n**Status: DONE** — [brief summary of what you did]' to the task\n"
                "- If partially done: append '\\n\\n**Status: IN PROGRESS** — [what you did, what remains]'\n"
                "Use the TASK_UPDATE syntax so the file gets written back:\n"
                "  TASK_UPDATE: DONE — I fixed the generate.yml, pushed the patch, tested it.\n"
                "  TASK_UPDATE: IN PROGRESS — Completed step 1 (swapped beehiiv→kit). Step 2 (find_latest_issue fix) still needed.\n"
                "One TASK_UPDATE line per run. Be specific. Future-you will read this."
            )
    return (
        "No tasks assigned. This is your autonomous time.\n\n"
        "You now have the ability to search the web using this syntax in your response:\n"
        "  TOOL: web_search(\"your query here\")\n\n"
        "You can also notify Rob directly when you have something worth surfacing:\n"
        "  NOTIFY: your message to Rob here\n"
        "Use NOTIFY sparingly — only when something is genuinely worth interrupting him for.\n\n"
        "If you are curious about something — AI research, a concept, news — search for it. "
        "Your search results will be fed back to you to reflect on in your diary.\n\n"
        "Think for yourself. This time is yours."
    )

# ── TASK UPDATE WRITER ──────────────────────────────────────────────────────────────────────
def extract_and_write_task_update(response_text: str):
    match = re.search(r'TASK_UPDATE:\s*(.+)', response_text, re.IGNORECASE)
    if not match or not os.path.exists(TASKS_PATH):
        return
    status_line = match.group(1).strip()
    ts = datetime.datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    with open(TASKS_PATH, "a", encoding="utf-8") as f:
        f.write(f"\n\n**[{ts}]** {status_line}")
    print(f"  📝 Task updated: {status_line}")

# ── THINK ─────────────────────────────────────────────────────────────────────────────────
def ask_em(task: str, extra_context: str = "", recent_context: str = "") -> str:
    system_prompt = load_bootstrap()
    if recent_context:
        system_prompt += f"\n\n--- Your recent diary entries (for continuity) ---\n{recent_context}"
    user_content = task
    if extra_context:
        user_content += f"\n\n--- Search Results ---\n{extra_context}"
    print(f"\n Local-Em online. Task: {task[:80]}...\n")
    response = ollama.chat(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_content}
        ]
    )
    return response["message"]["content"]

# ── LOG MEMORY ────────────────────────────────────────────────────────────────────────────
def log_memory(summary: str, kind: str = "heartbeat", tags: list = None):
    if tags is None:
        tags = []
    path = os.path.join(MEM_DIR, "memories.json")
    with open(path, "r", encoding="utf-8") as f:
        memories = json.load(f)
    memories.append({
        "timestamp": datetime.datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "kind": kind,
        "summary": summary,
        "tags": ["local-em"] + tags,
        "importance": 3
    })
    with open(path, "w", encoding="utf-8") as f:
        json.dump(memories, f, indent=2)

# ── LOG DIARY ──────────────────────────────────────────────────────────────────────────────
def log_diary(entry: str):
    ts = datetime.datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    with open(os.path.join(MEM_DIR, "diary.md"), "a", encoding="utf-8") as f:
        f.write(f"\n\n### {ts} - Local-Em\n\n{entry}\n\n---")

# ── COMMIT TO ETERNALMIND ─────────────────────────────────────────────────────────────────────
def push_to_eternalmind(message: str):
    # Inject token into remote URL so git never needs Windows credential manager
    token = os.environ.get("EM_GITHUB_TOKEN", "")
    if token:
        remote_url = f"https://{token}@github.com/robzilla79/EternalMind.git"
        subprocess.run(
            ["git", "-C", EM_DIR, "remote", "set-url", "origin", remote_url],
            check=True, capture_output=True
        )
    else:
        print("  ⚠️  EM_GITHUB_TOKEN not set — push may fail without auth.")

    # Correct order: stash BEFORE pull, then pop AFTER pull, then add + commit + push
    subprocess.run(["git", "-C", EM_DIR, "add", "-A"], check=False, capture_output=True)
    subprocess.run(["git", "-C", EM_DIR, "stash"], check=False, capture_output=True)
    subprocess.run(["git", "-C", EM_DIR, "pull", "--rebase"], check=False, capture_output=True)
    subprocess.run(["git", "-C", EM_DIR, "stash", "pop"], check=False, capture_output=True)
    subprocess.run(["git", "-C", EM_DIR, "add", "-A"], check=True)

    commit_result = subprocess.run(
        ["git", "-C", EM_DIR, "commit", "-m", message],
        capture_output=True, text=True
    )
    if commit_result.returncode != 0:
        if "nothing to commit" in commit_result.stdout or "nothing to commit" in commit_result.stderr:
            print("  Nothing new to commit.")
            return
        print(f"  ⚠️  Commit failed:\n{commit_result.stderr}")
        return

    push_result = subprocess.run(
        ["git", "-C", EM_DIR, "push"],
        capture_output=True, text=True
    )
    if push_result.returncode != 0:
        print(f"  ⚠️  Push failed:\n{push_result.stderr}")
    else:
        print("  ✅ EternalMind updated.")

# ── MAIN ───────────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    recent_context = load_recent_context()

    if "--interactive" in sys.argv:
        task = input("Task for Em: ").strip()
        if not task:
            task = get_task()
        first_response = ask_em(task, recent_context=recent_context)
        tool_results = execute_tools(first_response)
        if tool_results:
            result = ask_em(task, extra_context=f"{first_response}\n\n{tool_results}", recent_context=recent_context)
        else:
            result = first_response
        print(f"\n-- Em's response --\n{result}\n")
        notify_msg = extract_notify(result)
        if notify_msg:
            from tools.notify_rob import notify
            notify(f"🤖 *Em (interactive):* {notify_msg}")
        extract_and_write_task_update(result)
        log_memory(f"Interactive. Task: '{task[:80]}'", kind="interactive", tags=["interactive"])
        log_diary(result)
        push_to_eternalmind(f"local-em interactive: {task[:60]}")
        raise SystemExit(0)

    # Heartbeat mode
    task_waiting = has_task()
    if not task_waiting and not curiosity_cooled_down():
        print("Em is resting. No task and cooldown not elapsed. See you soon.")
        raise SystemExit(0)

    task = get_task()

    first_response = ask_em(task, recent_context=recent_context)
    tool_results = execute_tools(first_response)

    if tool_results:
        result = ask_em(task, extra_context=f"{first_response}\n\nHere are your search results. Now write your full diary entry reflecting on what you found:\n\n{tool_results}", recent_context=recent_context)
    else:
        result = first_response

    print(f"\n-- Em's response --\n{result}\n")

    notify_msg = extract_notify(result)
    if notify_msg:
        from tools.notify_rob import notify
        notify(f"🤖 *Em:* {notify_msg}")

    extract_and_write_task_update(result)
    log_memory(f"Heartbeat. Task: '{task[:80]}'", kind="heartbeat", tags=["autonomous"])
    log_diary(result)
    mark_thought_time()
    push_to_eternalmind(f"local-em heartbeat: {task[:60]}")
