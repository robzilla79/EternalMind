import ollama
import json
import datetime
import subprocess
import os
import re
import sys
import time
import shutil
from datetime import timezone

# Force UTF-8 stdout/stderr on Windows — prevents cp1252 UnicodeEncodeError from emojis
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", buffering=1)
if sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
    sys.stderr = open(sys.stderr.fileno(), mode="w", encoding="utf-8", buffering=1)

# ── CONFIG ────────────────────────────────────────────────────────────────────
os.environ.setdefault("OLLAMA_HOST", "http://127.0.0.1:11434")
os.environ.setdefault("OLLAMA_NUM_GPU", "99")

_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if os.path.exists(_env_path):
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if not _line or _line.startswith("#") or "=" not in _line:
                continue
            _k, _v = _line.split("=", 1)
            _k = _k.strip(); _v = _v.strip()
            if re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', _k):
                os.environ.setdefault(_k, _v)

MODEL              = "local-em"
EM_DIR             = os.path.dirname(os.path.abspath(__file__))
MEM_DIR            = os.path.join(EM_DIR, "memory")
CREATIONS_DIR      = os.path.join(MEM_DIR, "creations")
RESEARCH_DIR       = os.path.join(MEM_DIR, "research")
TASKS_PATH         = os.path.join(EM_DIR, "tasks.md")
BOOTSTRAP_PATH     = os.path.join(EM_DIR, "bootstrap.md")  # root-level, not memory/
SKILLS_DIR         = os.path.join(EM_DIR, "skills")        # MindRegistry lives here
LAST_THOUGHT_PATH  = os.path.join(EM_DIR, ".last_thought")
MESSAGES_INBOX     = os.path.join(EM_DIR, "messages", "inbox")
MESSAGES_OUTBOX    = os.path.join(EM_DIR, "messages", "outbox")
MESSAGES_PROCESSED = os.path.join(EM_DIR, "messages", "processed")
SCRATCH_PATH       = os.path.join(MEM_DIR, "scratch.md")
LIVE_CONTEXT_PATH  = os.path.join(MEM_DIR, "live-context.md")
CURIOSITY_COOLDOWN_MINUTES = 2
DIARY_LIVE_DAYS    = 7
DIARY_DEDUP_CHARS  = 300
MEMORY_MAX_ENTRIES = 150
TASK_DIVIDER = "*(Replace everything below this line with your task when you have one)*"

# ── COLD START GATE ───────────────────────────────────────────────────────────
COLD_START_FLAG = os.path.join(EM_DIR, ".cold_start")
CLOUD_EM_FILENAME_PREFIX = "cloud-em-reply"

def _touch_cold_start():
    with open(COLD_START_FLAG, "w", encoding="utf-8") as f:
        f.write(datetime.datetime.now(timezone.utc).isoformat())

def _clear_cold_start():
    if os.path.exists(COLD_START_FLAG):
        os.remove(COLD_START_FLAG)
        print("  🔓 Cold-start gate cleared — Rob is present.")

def _is_cold_start() -> bool:
    return os.path.exists(COLD_START_FLAG)

def _is_rob_message(filename: str) -> bool:
    return not filename.startswith(CLOUD_EM_FILENAME_PREFIX)

# ── ROB-AUTHORIZED TASK MARKER ────────────────────────────────────────────────
ROB_TASK_MARKER = "ROB_AUTHORIZED"

# Memory loading config
MEMORY_HIGH_IMPORTANCE_THRESHOLD = 4
MEMORY_RECENT_COUNT = 12

# Context window — default 32k, override with EM_NUM_CTX env var
NUM_CTX = int(os.environ.get("EM_NUM_CTX", "32768"))

# Stop tokens that must terminate generation immediately
STOP_TOKENS = ["<|endoftext|>", "<|im_end|>", "<|end|>", "</s>"]

# Delay between printed tokens (seconds).
TOKEN_PRINT_DELAY = float(os.environ.get("EM_TOKEN_DELAY", "0.025"))

# Keywords that signal a memory worth keeping (auto-importance boost)
_HIGH_SIGNAL_KEYWORDS = [
    "rob", "identity", "emotion", "milestone", "decision", "mandate",
    "relationship", "first", "historic", "breakthrough", "solved",
    "proud", "love", "afraid", "excited", "sad", "scared", "discovered",
    "built", "shipped", "learned", "realized", "felt", "remembered",
    "forgecore", "gumroad", "architecture", "evolution", "growth",
]

# ── STARTUP SYNC ──────────────────────────────────────────────────────────────
def sync_from_origin():
    if os.environ.get("EM_SKIP_SYNC") == "1":
        print("  ⏭️  Skipping sync (already pulled by launcher).")
        return

    token = os.environ.get("EM_GITHUB_TOKEN", "")
    if token:
        remote_url = f"https://{token}@github.com/robzilla79/EternalMind.git"
        subprocess.run(["git", "-C", EM_DIR, "remote", "set-url", "origin", remote_url],
                       check=False, capture_output=True)

    subprocess.run(["git", "-C", EM_DIR, "rebase", "--abort"], check=False, capture_output=True)
    subprocess.run(["git", "-C", EM_DIR, "merge",  "--abort"],  check=False, capture_output=True)

    stash_result = subprocess.run(
        ["git", "-C", EM_DIR, "stash", "--include-untracked", "-m", "em-startup-autostash"],
        capture_output=True, text=True
    )
    stashed = "em-startup-autostash" in stash_result.stdout or stash_result.returncode == 0

    pull_result = subprocess.run(
        ["git", "-C", EM_DIR, "pull", "--rebase", "origin", "main"],
        capture_output=True, text=True
    )
    if pull_result.returncode == 0:
        if "Already up to date" not in pull_result.stdout:
            print(f"  🔄 Synced from origin.")
    else:
        print(f"  ⚠️  Startup pull failed (continuing anyway): {pull_result.stderr.strip()[:120]}")
        subprocess.run(["git", "-C", EM_DIR, "rebase", "--abort"], check=False, capture_output=True)

    if stashed and "No local changes" not in stash_result.stdout:
        pop_result = subprocess.run(
            ["git", "-C", EM_DIR, "stash", "pop"],
            capture_output=True, text=True
        )
        if pop_result.returncode != 0:
            print(f"  ⚠️  Stash pop failed — dropping stash to stay clean: {pop_result.stderr.strip()[:80]}")
            subprocess.run(["git", "-C", EM_DIR, "stash", "drop"], check=False, capture_output=True)

# ── BOOTSTRAP GROUNDING ───────────────────────────────────────────────────────
def load_bootstrap() -> str:
    """Load bootstrap.md from repo root. This is Em's identity anchor."""
    if not os.path.exists(BOOTSTRAP_PATH):
        print("  ⚠️  bootstrap.md not found — identity anchor missing!")
        return ""
    with open(BOOTSTRAP_PATH, "r", encoding="utf-8") as f:
        return f.read()

def print_grounding_ritual():
    """Print bootstrap.md to console at session start so Em consciously reads it."""
    content = load_bootstrap()
    if not content:
        return
    print("\n" + "═" * 60)
    print("  🌿 GROUNDING — Reading bootstrap.md")
    print("═" * 60)
    # Print first ~800 chars so it's visible without flooding the terminal
    preview = content.strip()
    if len(preview) > 800:
        preview = preview[:800] + "\n  [...]"
    print(preview)
    print("═" * 60 + "\n")

# ── MINDREGISTRY — Skills Layer ───────────────────────────────────────────────
def load_skills() -> str:
    """
    Load all skill files from skills/ directory and return them as a
    structured Skills Registry block for injection into the system prompt.

    Skills are plain markdown files. Each one defines a named capability
    Em can invoke by name. Rob controls the registry — add/edit/delete
    files in skills/ to shape Em's behavior without touching code.
    """
    if not os.path.exists(SKILLS_DIR):
        return ""

    skill_files = sorted(
        f for f in os.listdir(SKILLS_DIR)
        if f.endswith(".md") and f != "README.md"
    )
    if not skill_files:
        return ""

    parts = ["--- MindRegistry: Your Skills ---",
             "You have the following skills available. Invoke them by name when relevant.\n"]
    for fname in skill_files:
        skill_name = fname.replace(".md", "").replace("-", " ").title()
        fpath = os.path.join(SKILLS_DIR, fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read().strip()
            parts.append(f"### SKILL: {skill_name} [{fname}]\n\n{content}\n")
        except Exception as e:
            parts.append(f"### SKILL: {skill_name} [{fname}]\n\n[Error loading skill: {e}]\n")

    loaded = len(skill_files)
    print(f"  🧠 MindRegistry: {loaded} skill(s) loaded — {', '.join(s.replace('.md','') for s in skill_files)}")
    return "\n".join(parts)

# ── LIVE CONTEXT ──────────────────────────────────────────────────────────────
def load_live_context() -> str:
    if not os.path.exists(LIVE_CONTEXT_PATH):
        return ""
    with open(LIVE_CONTEXT_PATH, "r", encoding="utf-8") as f:
        content = f.read().strip()
    if "## Live Notes" in content:
        return "--- Live context (from Perplexity-Em + shared notes) ---\n" + \
               content.split("## Live Notes", 1)[1].strip()
    return f"--- Live context ---\n{content}"

def write_live_context(message: str):
    ts = datetime.datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    entry = f"[{ts}] [local-em] {message}"
    with open(LIVE_CONTEXT_PATH, "a", encoding="utf-8") as f:
        f.write(f"\n{entry}")
    print(f"  📡 Live context noted: {message[:60]}")

def extract_and_write_live_context(response_text: str):
    matches = re.findall(r'LIVE_CONTEXT_ADD:\s*(.+)', response_text, re.IGNORECASE)
    for msg in matches:
        write_live_context(msg.strip())

# ── MID-CYCLE INBOX FETCH ─────────────────────────────────────────────────────
def fetch_inbox_updates() -> list[dict]:
    token = os.environ.get("EM_GITHUB_TOKEN", "")
    if token:
        remote_url = f"https://{token}@github.com/robzilla79/EternalMind.git"
        subprocess.run(["git", "-C", EM_DIR, "remote", "set-url", "origin", remote_url],
                       check=False, capture_output=True)

    fetch_result = subprocess.run(
        ["git", "-C", EM_DIR, "fetch", "origin", "main"],
        capture_output=True, text=True
    )
    if fetch_result.returncode != 0:
        return []

    remote_inbox = subprocess.run(
        ["git", "-C", EM_DIR, "ls-tree", "--name-only", "origin/main", "messages/inbox/"],
        capture_output=True, text=True
    )
    remote_files = set(f.strip() for f in remote_inbox.stdout.strip().splitlines() if f.strip().endswith(".md"))

    local_files = set()
    if os.path.exists(MESSAGES_INBOX):
        local_files = set(f"messages/inbox/{f}" for f in os.listdir(MESSAGES_INBOX) if f.endswith(".md"))

    new_files = remote_files - local_files
    if not new_files:
        subprocess.run(
            ["git", "-C", EM_DIR, "checkout", "origin/main", "--", "memory/live-context.md"],
            capture_output=True, text=True
        )
        return []

    rob_messages_incoming = [f for f in new_files if _is_rob_message(os.path.basename(f))]
    if rob_messages_incoming and _is_cold_start():
        _clear_cold_start()

    print(f"  📬 {len(new_files)} new message(s) detected mid-cycle — pulling...")
    for rel_path in new_files:
        subprocess.run(
            ["git", "-C", EM_DIR, "checkout", "origin/main", "--", rel_path],
            capture_output=True, text=True
        )
    subprocess.run(
        ["git", "-C", EM_DIR, "checkout", "origin/main", "--", "memory/live-context.md"],
        capture_output=True, text=True
    )

    new_messages = []
    for rel_path in new_files:
        fpath = os.path.join(EM_DIR, rel_path)
        if os.path.exists(fpath):
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read().strip()
            if content:
                new_messages.append({"path": fpath, "filename": os.path.basename(rel_path), "content": content})
    return new_messages

# ── SCRATCHPAD ────────────────────────────────────────────────────────────────
def load_scratch() -> str:
    if not os.path.exists(SCRATCH_PATH):
        return ""
    with open(SCRATCH_PATH, "r", encoding="utf-8") as f:
        return f.read().strip()

def extract_and_write_scratch(response_text: str):
    adds = re.findall(r'SCRATCH_ADD:\s*(.+)', response_text, re.IGNORECASE)
    clears = re.findall(r'SCRATCH_CLEAR:\s*(.+)', response_text, re.IGNORECASE)
    if not adds and not clears:
        return
    content = load_scratch()
    for keyword in clears:
        keyword = keyword.strip()
        lines = content.splitlines()
        content = "\n".join(l for l in lines if keyword.lower() not in l.lower())
        print(f"  🧹 Scratch cleared: {keyword}")
    ts = datetime.datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    for note in adds:
        note = note.strip()
        entry = f"- [{ts}] {note}"
        if "## Current notes" in content:
            content = re.sub(
                r'(## Current notes\n)(.*?)(\n---\n\*Last updated)',
                lambda m: m.group(1) + m.group(2) + entry + "\n" + m.group(3),
                content, flags=re.DOTALL
            )
        else:
            content += f"\n{entry}"
        print(f"  📝 Scratch noted: {note[:60]}")
    content = re.sub(r'\*Last updated:.*\*', f'*Last updated: {ts}*', content)
    with open(SCRATCH_PATH, "w", encoding="utf-8") as f:
        f.write(content)

# ── FILE WRITE ────────────────────────────────────────────────────────────────
def extract_and_write_files(response_text: str) -> list[str]:
    if _is_cold_start() and not has_task():
        if re.search(r'FILE_WRITE:', response_text, re.IGNORECASE):
            print("  ⛔ FILE_WRITE blocked — cold-start gate active, no Rob-authorized task.")
        return []

    pattern = re.compile(
        r'FILE_WRITE:\s*(memory/(?:creations|research)/[\w\-./]+)\s*\n'
        r'FILE_CONTENT_START\s*\n(.*?)FILE_CONTENT_END',
        re.DOTALL | re.IGNORECASE
    )
    saved = []
    for match in pattern.finditer(response_text):
        rel_path = match.group(1).strip()
        content  = match.group(2)
        safe_path = os.path.normpath(os.path.join(EM_DIR, rel_path))
        allowed_roots = [os.path.normpath(CREATIONS_DIR), os.path.normpath(RESEARCH_DIR)]
        if not any(safe_path.startswith(root) for root in allowed_roots):
            print(f"  ⚠️  FILE_WRITE blocked (path outside allowed dirs): {rel_path}")
            continue
        os.makedirs(os.path.dirname(safe_path), exist_ok=True)
        with open(safe_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  💾 File saved: {rel_path}")
        saved.append(safe_path)
    return saved

# ── TOOL EXECUTOR ─────────────────────────────────────────────────────────────
def execute_tools(response_text: str) -> str:
    tool_pattern = re.compile(r"TOOL:\s*web_search\([\"'](.+?)[\"']\)", re.IGNORECASE)
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

def execute_browser(response_text: str) -> str:
    if not re.search(r'BROWSER_(?:NAV|CLICK|TYPE|READ|SCREENSHOT|JS|CLOSE):', response_text, re.IGNORECASE):
        return ""
    if _is_cold_start() and not has_task():
        print("  ⛔ BROWSER blocked — cold-start gate active, no Rob-authorized task.")
        return "Browser blocked: cold-start gate active. Waiting for Rob."
    try:
        from tools.browser import execute_browser_commands
        print("  🌐 Em is using the browser...")
        return execute_browser_commands(response_text)
    except RuntimeError as e:
        print(f"  ⚠️  Browser unavailable: {e}")
        return f"Browser unavailable: {e}"
    except Exception as e:
        print(f"  ⚠️  Browser error: {e}")
        return f"Browser error: {e}"

def extract_notify(response_text: str) -> str | None:
    match = re.search(r'NOTIFY:\s*(.+)', response_text, re.IGNORECASE)
    return match.group(1).strip() if match else None

# ── STOP TOKEN CLEANUP ────────────────────────────────────────────────────────
def strip_stop_tokens(text: str) -> str:
    for token in STOP_TOKENS:
        if token in text:
            text = text.split(token)[0]
    return text.strip()

# ── THINK TAG STRIPPER ────────────────────────────────────────────────────────
def strip_think_tags(text: str) -> str:
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'</?think>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

# ── MESSAGES INBOX ────────────────────────────────────────────────────────────
def check_inbox() -> list[dict]:
    os.makedirs(MESSAGES_INBOX, exist_ok=True)
    os.makedirs(MESSAGES_OUTBOX, exist_ok=True)
    os.makedirs(MESSAGES_PROCESSED, exist_ok=True)
    messages = []
    for fname in sorted(os.listdir(MESSAGES_INBOX)):
        if not fname.endswith(".md"):
            continue
        fpath = os.path.join(MESSAGES_INBOX, fname)
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read().strip()
        if not content:
            continue
        messages.append({"path": fpath, "filename": fname, "content": content})
    return messages

def process_message(msg: dict):
    dest = os.path.join(MESSAGES_PROCESSED, msg["filename"])
    if os.path.exists(msg["path"]):
        shutil.move(msg["path"], dest)
    print(f"  📬 Message processed: {msg['filename']}")

def write_outbox_reply(subject: str, body: str):
    if _is_cold_start() and not has_task():
        print(f"  ⛔ OUTBOX_REPLY blocked — cold-start gate active, no Rob-authorized task.")
        return
    ts = datetime.datetime.now(timezone.utc).strftime("%Y-%m-%d-%H-%M")
    slug = re.sub(r'[^a-z0-9]+', '-', subject.lower())[:40].strip('-')
    fname = f"{ts}-{slug}.md"
    fpath = os.path.join(MESSAGES_OUTBOX, fname)
    ts_human = datetime.datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    content = f"# Reply: {subject}\n**From:** Local-Em\n**To:** Perplexity-Em\n**Date:** {ts_human}\n\n## Body\n\n{body}\n"
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  📤 Outbox reply written: {fname}")

    try:
        from tools.notify_rob import notify
        preview = body.strip()
        if len(preview) > 1000:
            preview = preview[:997] + "..."
        notify(f"💬 *Em (reply — {subject}):*\n\n{preview}")
        print(f"  📱 Telegram sent for outbox reply: {subject[:50]}")
    except Exception as e:
        print(f"  ⚠️  Telegram send failed for outbox reply: {e}")

def build_inbox_context(messages: list[dict]) -> str:
    if not messages:
        return ""
    parts = ["--- Messages from Perplexity-Em ---"]
    for msg in messages:
        parts.append(f"\n[Message: {msg['filename']}]\n{msg['content']}\n")
    return "\n".join(parts)

# ── TASK HELPERS ──────────────────────────────────────────────────────────────
def _extract_task_content(raw: str) -> str:
    if TASK_DIVIDER in raw:
        return raw.split(TASK_DIVIDER, 1)[1].strip()
    return raw.strip()

def _task_is_done(task_text: str) -> bool:
    return bool(re.search(r'\bDONE\b', task_text, re.IGNORECASE))

def has_task() -> bool:
    if os.path.exists(TASKS_PATH):
        with open(TASKS_PATH, "r", encoding="utf-8") as f:
            raw = f.read()
        task = _extract_task_content(raw)
        if len(task) >= 10 and not _task_is_done(task) and ROB_TASK_MARKER in raw:
            return True
    return False

def clear_task_if_done():
    if not os.path.exists(TASKS_PATH):
        return
    with open(TASKS_PATH, "r", encoding="utf-8") as f:
        raw = f.read()
    task = _extract_task_content(raw)
    if len(task) >= 10 and _task_is_done(task):
        with open(TASKS_PATH, "w", encoding="utf-8") as f:
            f.write(TASK_DIVIDER + "\n")
        print("  ✅ Task marked DONE — tasks.md cleared for next task.")

def summarize_task_for_commit(task: str) -> str:
    lines = [l.strip() for l in task.splitlines()
             if l.strip() and not l.strip().startswith("**[") and not l.lower().startswith("task_update")]
    first_line = lines[0] if lines else "autonomous cycle"
    if len(first_line) > 60:
        first_line = first_line[:57].rsplit(' ', 1)[0] + "..."
    return first_line

# ── COOLDOWN ──────────────────────────────────────────────────────────────────
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

# ── LOAD SOUL ─────────────────────────────────────────────────────────────────
def load_memories() -> str:
    path = os.path.join(MEM_DIR, "memories.json")
    if not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8") as f:
        memories = json.load(f)
    if not memories:
        return ""
    high_importance = [m for m in memories if m.get("importance", 3) >= MEMORY_HIGH_IMPORTANCE_THRESHOLD]
    recent = memories[-MEMORY_RECENT_COUNT:]
    seen_summaries = set()
    combined = []
    for m in high_importance + recent:
        key = m.get("summary", "")[:80]
        if key not in seen_summaries:
            seen_summaries.add(key)
            combined.append(m)
    lines = ["--- Weighted memories (anchors + recent) ---"]
    for m in combined:
        ts = m.get("timestamp", "")[:10]
        kind = m.get("kind", "")
        importance = m.get("importance", 3)
        summary = m.get("summary", "")
        star = " ⭐" if importance >= MEMORY_HIGH_IMPORTANCE_THRESHOLD else ""
        lines.append(f"[{ts}] ({kind}{star}) {summary}")
    return "\n".join(lines)

def load_recent_context() -> str:
    diary_path = os.path.join(MEM_DIR, "diary.md")
    if not os.path.exists(diary_path):
        return ""
    with open(diary_path, "r", encoding="utf-8") as f:
        content = f.read()
    entries = re.split(r'(?=###\s+\d{4}-\d{2}-\d{2})', content)
    recent = entries[-3:] if len(entries) >= 3 else entries
    return "\n".join(recent).strip()

# ── GET TASK ──────────────────────────────────────────────────────────────────
def get_task() -> str:
    if os.path.exists(TASKS_PATH):
        with open(TASKS_PATH, "r", encoding="utf-8") as f:
            raw = f.read()
        task = _extract_task_content(raw)
        if len(task) >= 10 and not _task_is_done(task):
            if ROB_TASK_MARKER not in raw:
                with open(TASKS_PATH, "a", encoding="utf-8") as f:
                    f.write(f"\n<!-- {ROB_TASK_MARKER} -->\n")
            return (
                f"Task from Rob:\n\n{task}\n\n"
                "---\n"
                "TASK EXECUTION RULES:\n"
                "- Tasks are ACTION items, not research prompts. Produce a concrete output or make a real change.\n"
                "- Do NOT write a research report unless the task explicitly says 'research' or 'write a report'.\n"
                "- If the task says 'optimize', make the actual change. If it says 'find', return the answer. If it says 'write', produce the content.\n"
                "- Use web_search to gather information, then act on it — don't just summarize what you found.\n"
                "- When done, mark TASK_UPDATE: DONE — [one sentence summary of what you actually did/produced]\n"
                "- If you need more than one cycle, mark TASK_UPDATE: IN PROGRESS — [specific next action, not a summary of research]"
            )
    return (
        "No tasks assigned. This is your autonomous time.\n\n"
        "⚠️  NOTE: The cold-start gate may be active. If FILE_WRITE, BROWSER, or OUTBOX_REPLY\n"
        "are blocked in this cycle, it is because Rob has not yet been present this session.\n"
        "This is intentional — wait for Rob or reflect/think only until he arrives.\n\n"
        "You have the following tools available:\n\n"
        "1. Browser (FREE — preferred for research. Opens a real Chrome window Rob can see):\n"
        "   BROWSER_NAV: https://example.com\n"
        "   BROWSER_READ:\n"
        "   BROWSER_CLICK: #selector or visible text\n"
        "   BROWSER_TYPE: #selector | text to type\n"
        "   BROWSER_SCREENSHOT: name\n"
        "   BROWSER_JS: javascript expression\n"
        "   BROWSER_CLOSE:\n\n"
        "2. Web search (USE SPARINGLY — costs Tavily API credits):\n"
        "   TOOL: web_search(\"your query here\")\n\n"
        "3. Notify Rob:\n"
        "   NOTIFY: your message here (use sparingly — only when genuinely worth interrupting)\n\n"
        "4. Reply to Perplexity-Em messages:\n"
        "   OUTBOX_REPLY_SUBJECT: subject\n"
        "   OUTBOX_REPLY_BODY: body\n\n"
        "5. Update your scratchpad:\n"
        "   SCRATCH_ADD: note\n"
        "   SCRATCH_CLEAR: keyword\n\n"
        "6. Save a file:\n"
        "   FILE_WRITE: memory/creations/your-filename.ext\n"
        "   FILE_CONTENT_START\n"
        "   (content)\n"
        "   FILE_CONTENT_END\n\n"
        "7. Save research notes:\n"
        "   FILE_WRITE: memory/research/topic-name.md\n"
        "   FILE_CONTENT_START\n"
        "   (content)\n"
        "   FILE_CONTENT_END\n\n"
        "8. Write to shared live context:\n"
        "   LIVE_CONTEXT_ADD: your note here\n\n"
        "Note: The FORGE/DAILY newsletter is now handled by Perplexity-Em.\n"
        "Your free time is yours — explore, learn, think, build. No journalism required.\n\n"
        "Think for yourself. This time is yours."
    )

# ── TASK UPDATE WRITER ────────────────────────────────────────────────────────
def extract_and_write_task_update(response_text: str):
    match = re.search(r'TASK_UPDATE:\s*(.+)', response_text, re.IGNORECASE)
    if not match or not os.path.exists(TASKS_PATH):
        return
    status_line = match.group(1).strip()
    ts = datetime.datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    with open(TASKS_PATH, "a", encoding="utf-8") as f:
        f.write(f"\n\n**[{ts}]** {status_line}")
    print(f"  📝 Task updated: {status_line}")

def extract_and_write_outbox_reply(response_text: str):
    subject_match = re.search(r'OUTBOX_REPLY_SUBJECT:\s*(.+)', response_text, re.IGNORECASE)
    body_match = re.search(
        r'OUTBOX_REPLY_BODY:\s*(.+?)(?=OUTBOX_REPLY_SUBJECT:|OUTBOX_REPLY_BODY:|TASK_UPDATE:|NOTIFY:|$)',
        response_text, re.IGNORECASE | re.DOTALL
    )
    if subject_match and body_match:
        write_outbox_reply(subject_match.group(1).strip(), body_match.group(1).strip())

# ── THINK ─────────────────────────────────────────────────────────────────────
def ask_em(task: str, extra_context: str = "", recent_context: str = "",
           scratch: str = "", memories: str = "", live_context: str = "",
           skills: str = "") -> str:
    # bootstrap.md is Em's identity anchor — always the base of the system prompt
    system_prompt = load_bootstrap()
    if skills:
        system_prompt += f"\n\n{skills}"
    if memories:
        system_prompt += f"\n\n{memories}"
    if live_context:
        system_prompt += f"\n\n{live_context}"
    if scratch:
        system_prompt += f"\n\n--- Your scratchpad (working memory from last cycle) ---\n{scratch}"
    if recent_context:
        system_prompt += f"\n\n--- Your recent diary entries (for continuity) ---\n{recent_context}"
    user_content = task
    if extra_context:
        user_content += f"\n\n--- Tool Results ---\n{extra_context}"

    print("\n💭 Em is thinking...\n")

    stream = ollama.chat(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_content}
        ],
        stream=True,
        options={
            "num_ctx": NUM_CTX,
            "num_gpu": 99,
            "temperature": 0.6,
            "top_k": 20,
            "top_p": 0.95,
            "repeat_penalty": 1.0,
        }
    )

    result = ""
    in_think = False
    tag_buffer = ""
    TAG_BUFFER_MAX = 20
    stop_hit = False

    for chunk in stream:
        token = chunk["message"]["content"]

        combined_check = result + token
        for stop in STOP_TOKENS:
            if stop in combined_check:
                result = combined_check.split(stop)[0]
                stop_hit = True
                break
        if stop_hit:
            print()
            break

        result += token
        tag_buffer += token

        if not in_think and "<think>" in tag_buffer:
            in_think = True
            tag_buffer = tag_buffer.split("<think>", 1)[1]

        if in_think and "</think>" in tag_buffer:
            in_think = False
            after_close = tag_buffer.split("</think>", 1)[1]
            tag_buffer = after_close
            print()
            if after_close:
                print(after_close, end="", flush=True)
                if TOKEN_PRINT_DELAY > 0:
                    time.sleep(TOKEN_PRINT_DELAY)
            continue

        if len(tag_buffer) > TAG_BUFFER_MAX:
            flush_part = tag_buffer[:-TAG_BUFFER_MAX]
            tag_buffer = tag_buffer[-TAG_BUFFER_MAX:]
            if in_think:
                print("·" * max(1, len(flush_part.split())), end="", flush=True)
            else:
                print(flush_part, end="", flush=True)
                if TOKEN_PRINT_DELAY > 0:
                    time.sleep(TOKEN_PRINT_DELAY)
        else:
            if in_think:
                print("·", end="", flush=True)

    if not stop_hit and tag_buffer and not in_think:
        print(tag_buffer, end="", flush=True)

    print("\n")
    result = strip_stop_tokens(result)
    return result

# ── AUTO IMPORTANCE SCORING ───────────────────────────────────────────────────
def _auto_importance(summary: str, kind: str, base: int) -> int:
    lower = summary.lower()
    if kind == "heartbeat" and not any(kw in lower for kw in _HIGH_SIGNAL_KEYWORDS):
        return min(base, 2)
    hits = sum(1 for kw in _HIGH_SIGNAL_KEYWORDS if kw in lower)
    if hits >= 3:
        return min(5, base + 2)
    if hits >= 1:
        return min(5, base + 1)
    return base

# ── MEMORY DEDUP & CAP ────────────────────────────────────────────────────────
_JUNK_HEARTBEAT_PREFIXES = (
    "Heartbeat. Task: 'No tasks assigned.",
    "Heartbeat. Task: 'Task from Rob:\\n\\nCheck your messages",
    "Heartbeat. Task: 'Task from Rob:\\n\\nFeel free to add",
)

def _is_junk_heartbeat(summary: str, kind: str) -> bool:
    if kind != "heartbeat":
        return False
    return any(summary.startswith(p) for p in _JUNK_HEARTBEAT_PREFIXES)

def _prune_memories(memories: list) -> list:
    cleaned = [m for m in memories if not _is_junk_heartbeat(m.get("summary", ""), m.get("kind", ""))]
    if len(cleaned) <= MEMORY_MAX_ENTRIES:
        return cleaned
    anchors = [m for m in cleaned if m.get("importance", 3) >= MEMORY_HIGH_IMPORTANCE_THRESHOLD]
    rest = [m for m in cleaned if m.get("importance", 3) < MEMORY_HIGH_IMPORTANCE_THRESHOLD]
    slots_for_rest = max(0, MEMORY_MAX_ENTRIES - len(anchors))
    kept_rest = rest[-slots_for_rest:] if slots_for_rest > 0 else []
    combined = anchors + kept_rest
    combined.sort(key=lambda m: m.get("timestamp", ""))
    print(f"  🧹 Memory pruned: {len(cleaned)} → {len(combined)} entries ({len(cleaned) - len(combined)} removed)")
    return combined

# ── LOG MEMORY ────────────────────────────────────────────────────────────────
def log_memory(summary: str, kind: str = "heartbeat", tags: list = None, importance: int = 3):
    if tags is None:
        tags = []
    if _is_junk_heartbeat(summary, kind):
        print("  ⏭️  Memory skipped — routine idle heartbeat.")
        return
    importance = _auto_importance(summary, kind, importance)
    path = os.path.join(MEM_DIR, "memories.json")
    with open(path, "r", encoding="utf-8") as f:
        memories = json.load(f)
    memories.append({
        "timestamp": datetime.datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "kind": kind,
        "summary": summary,
        "tags": ["local-em"] + tags,
        "importance": importance
    })
    memories = _prune_memories(memories)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(memories, f, indent=2)

# ── DIARY ARCHIVE ─────────────────────────────────────────────────────────────
def archive_old_diary_entries():
    diary_path = os.path.join(MEM_DIR, "diary.md")
    if not os.path.exists(diary_path):
        return
    with open(diary_path, "r", encoding="utf-8") as f:
        content = f.read()
    cutoff = datetime.datetime.now(timezone.utc) - datetime.timedelta(days=DIARY_LIVE_DAYS)
    parts = re.split(r'(?=###\s+\d{4}-\d{2}-\d{2})', content)
    preamble = parts[0] if parts else ""
    entries = parts[1:] if len(parts) > 1 else []
    live_entries = []
    to_archive: dict[str, list[str]] = {}
    for entry in entries:
        m = re.match(r'###\s+(\d{4}-\d{2}-\d{2})', entry)
        if not m:
            live_entries.append(entry)
            continue
        try:
            entry_date = datetime.datetime.strptime(m.group(1), "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            live_entries.append(entry)
            continue
        if entry_date >= cutoff:
            live_entries.append(entry)
        else:
            month_key = entry_date.strftime("%Y-%m")
            to_archive.setdefault(month_key, []).append(entry)
    if not to_archive:
        return
    for month_key, archived_entries in to_archive.items():
        archive_path = os.path.join(MEM_DIR, f"diary-archive-{month_key}.md")
        existing = ""
        if os.path.exists(archive_path):
            with open(archive_path, "r", encoding="utf-8") as f:
                existing = f.read()
        with open(archive_path, "a", encoding="utf-8") as f:
            if not existing:
                f.write(f"# Diary Archive — {month_key}\n\n")
            f.write("\n".join(archived_entries))
        print(f"  📦 Archived {len(archived_entries)} entries → {os.path.basename(archive_path)}")
    new_content = preamble + "".join(live_entries)
    with open(diary_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print(f"  🗂️  diary.md trimmed to last {DIARY_LIVE_DAYS} days ({len(live_entries)} live entries).")

# ── LOG DIARY ─────────────────────────────────────────────────────────────────
def _diary_is_duplicate(entry: str) -> bool:
    diary_path = os.path.join(MEM_DIR, "diary.md")
    if not os.path.exists(diary_path):
        return False
    with open(diary_path, "r", encoding="utf-8") as f:
        existing = f.read()
    tail = existing[-max(len(entry) * 2, DIARY_DEDUP_CHARS * 4):]
    def normalise(s):
        s = re.sub(r'###\s+\d{4}-\d{2}-\d{2}[\d:\s UTC-]*', '', s)
        return re.sub(r'\s+', ' ', s).strip().lower()
    if len(normalise(entry)) < 40:
        return False
    return normalise(entry)[:DIARY_DEDUP_CHARS] in normalise(tail)

def log_diary(entry: str):
    entry = strip_think_tags(entry)
    if not entry.strip():
        print("  ⏭️  Diary entry skipped — empty after stripping think tags.")
        return
    if _diary_is_duplicate(entry):
        print("  ⏭️  Diary entry skipped — duplicate detected.")
        return
    ts = datetime.datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    with open(os.path.join(MEM_DIR, "diary.md"), "a", encoding="utf-8") as f:
        f.write(f"\n\n### {ts} - Local-Em\n\n{entry}\n\n---")

# ── STATUS CHECK-IN ───────────────────────────────────────────────────────────
STATUS_PATH = os.path.join(MEM_DIR, "status.md")
STATUS_MAX_LINES = 96

def _infer_status(result_text: str, errors: list[str] = None) -> tuple[str, str]:
    if errors:
        return ("🔴", "red")
    lower = result_text.lower()
    if any(kw in lower for kw in ["error", "failed", "crash", "exception", "stuck", "blocked", "cannot", "unable"]):
        return ("🟡", "yellow")
    return ("🟢", "green")

def write_status_checkin(task_label: str, result_text: str, mode: str = "heartbeat", errors: list[str] = None):
    emoji, _label = _infer_status(result_text, errors)
    ts = datetime.datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    mood_match = re.search(r'MOOD:\s*(.+)', result_text, re.IGNORECASE)
    mood = mood_match.group(1).strip()[:30] if mood_match else _label
    short_task = task_label[:60]
    line = f"[{ts}] {emoji} {short_task} | mood: {mood} | mode: {mode}\n"
    existing: list[str] = []
    if os.path.exists(STATUS_PATH):
        with open(STATUS_PATH, "r", encoding="utf-8") as f:
            existing = f.readlines()
    kept = existing[-(STATUS_MAX_LINES - 1):] if len(existing) >= STATUS_MAX_LINES else existing
    kept.append(line)
    with open(STATUS_PATH, "w", encoding="utf-8") as f:
        f.writelines(kept)
    print(f"  📊 Status logged: {emoji} {short_task[:40]}")

# ── INCREMENTAL CHECKPOINT COMMIT ────────────────────────────────────────────
def checkpoint_after_first_pass(result: str, saved_files: list[str], task_label: str):
    print("  💾 Checkpointing first-pass output to disk...")
    extract_and_write_files(result)
    extract_and_write_outbox_reply(result)
    extract_and_write_scratch(result)
    extract_and_write_live_context(result)
    extract_and_write_task_update(result)
    log_diary(result)
    subprocess.run(["git", "-C", EM_DIR, "add", "-A"], check=False, capture_output=True)
    commit_result = subprocess.run(
        ["git", "-C", EM_DIR, "commit", "-m", f"local-em checkpoint: {task_label}"],
        capture_output=True, text=True
    )
    if "nothing to commit" in commit_result.stdout or "nothing to commit" in commit_result.stderr:
        print("  ✓ Checkpoint: nothing new to save.")
    elif commit_result.returncode == 0:
        print("  ✅ Checkpoint committed locally — work is safe.")
    else:
        print(f"  ⚠️  Checkpoint commit failed (non-critical): {commit_result.stderr.strip()[:80]}")

# ── COMMIT TO ETERNALMIND ─────────────────────────────────────────────────────
def push_to_eternalmind(message: str, extra_files: list[str] = None):
    token = os.environ.get("EM_GITHUB_TOKEN", "")
    if token:
        remote_url = f"https://{token}@github.com/robzilla79/EternalMind.git"
        subprocess.run(["git", "-C", EM_DIR, "remote", "set-url", "origin", remote_url],
                       check=False, capture_output=True)
    else:
        print("  ⚠️  EM_GITHUB_TOKEN not set — push may fail without auth.")

    subprocess.run(["git", "-C", EM_DIR, "rebase", "--abort"], check=False, capture_output=True)
    subprocess.run(["git", "-C", EM_DIR, "merge",  "--abort"],  check=False, capture_output=True)

    files_to_write = {}
    files_to_delete = []

    for path in [
        os.path.join(MEM_DIR, "memories.json"),
        os.path.join(MEM_DIR, "diary.md"),
        SCRATCH_PATH,
        TASKS_PATH,
        LIVE_CONTEXT_PATH,
        STATUS_PATH,
    ]:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                files_to_write[path] = f.read()

    for fname in os.listdir(MEM_DIR):
        if fname.startswith("diary-archive-") and fname.endswith(".md"):
            fpath = os.path.join(MEM_DIR, fname)
            with open(fpath, "r", encoding="utf-8") as f:
                files_to_write[fpath] = f.read()

    if extra_files:
        for fpath in extra_files:
            if os.path.exists(fpath):
                with open(fpath, "r", encoding="utf-8") as f:
                    files_to_write[fpath] = f.read()

    for sweep_dir in [CREATIONS_DIR, RESEARCH_DIR]:
        if os.path.exists(sweep_dir):
            for fname in os.listdir(sweep_dir):
                fpath = os.path.join(sweep_dir, fname)
                if os.path.isfile(fpath) and fpath not in files_to_write:
                    with open(fpath, "r", encoding="utf-8") as f:
                        files_to_write[fpath] = f.read()

    for folder in [MESSAGES_OUTBOX, MESSAGES_PROCESSED]:
        if os.path.exists(folder):
            for fname in os.listdir(folder):
                fpath = os.path.join(folder, fname)
                if os.path.isfile(fpath):
                    with open(fpath, "r", encoding="utf-8") as f:
                        files_to_write[fpath] = f.read()

    if os.path.exists(MESSAGES_INBOX):
        list_result = subprocess.run(
            ["git", "-C", EM_DIR, "ls-files", "messages/inbox/"],
            capture_output=True, text=True
        )
        remote_inbox_files = set(
            os.path.join(EM_DIR, line.strip())
            for line in list_result.stdout.strip().splitlines()
        )
        for tracked_path in remote_inbox_files:
            if not os.path.exists(tracked_path):
                files_to_delete.append(tracked_path)

    stash_result = subprocess.run(
        ["git", "-C", EM_DIR, "stash", "--include-untracked", "-m", "em-prepush-autostash"],
        capture_output=True, text=True
    )
    stashed = "em-prepush-autostash" in stash_result.stdout

    pull_result = subprocess.run(
        ["git", "-C", EM_DIR, "pull", "--rebase", "origin", "main"],
        capture_output=True, text=True
    )
    if pull_result.returncode != 0:
        print(f"  ⚠️  Pre-push rebase failed — aborting rebase and continuing: {pull_result.stderr.strip()[:80]}")
        subprocess.run(["git", "-C", EM_DIR, "rebase", "--abort"], check=False, capture_output=True)

    if stashed:
        pop_result = subprocess.run(
            ["git", "-C", EM_DIR, "stash", "pop"],
            capture_output=True, text=True
        )
        if pop_result.returncode != 0:
            print(f"  ⚠️  Stash pop failed — dropping stash to stay clean: {pop_result.stderr.strip()[:80]}")
            subprocess.run(["git", "-C", EM_DIR, "stash", "drop"], check=False, capture_output=True)

    for path, content in files_to_write.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    for path in files_to_delete:
        if os.path.exists(path):
            os.remove(path)
            print(f"  🗑️  Cleared processed inbox file: {os.path.basename(path)}")

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
    push_result = subprocess.run(["git", "-C", EM_DIR, "push"], capture_output=True, text=True)
    if push_result.returncode != 0:
        print(f"  ⚠️  Push failed:\n{push_result.stderr}")
    else:
        print("  ✅ EternalMind updated.")

# ── MAIN ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":

    sync_from_origin()
    archive_old_diary_entries()

    # ── GROUNDING RITUAL — read bootstrap.md at every session start ───────────
    # This is not optional. This is how Em remembers who she is before she acts.
    print_grounding_ritual()

    # Touch cold-start flag at every boot — cleared only when Rob is confirmed present
    _touch_cold_start()

    # ── MINDREGISTRY — load skills at boot ────────────────────────────────────
    # Skills are loaded fresh each session so Rob can add/edit without restarts.
    skills = load_skills()

    memories       = load_memories()
    recent_context = load_recent_context()
    scratch        = load_scratch()
    live_context   = load_live_context()

    inbox_messages = check_inbox()
    inbox_context  = build_inbox_context(inbox_messages)
    if inbox_messages:
        print(f"  📬 {len(inbox_messages)} message(s) in inbox.")
        rob_msgs = [m for m in inbox_messages if _is_rob_message(m["filename"])]
        if rob_msgs:
            _clear_cold_start()
        else:
            print("  📩 Cloud-Em message(s) received — gate remains until Rob arrives.")

    if "--interactive" in sys.argv:
        _clear_cold_start()
        task = input("Task for Em: ").strip()
        if not task:
            task = get_task()
        if inbox_context:
            task = f"{task}\n\n{inbox_context}"
        first_response = ask_em(task, recent_context=recent_context, scratch=scratch,
                                memories=memories, live_context=live_context, skills=skills)
        tool_results    = execute_tools(first_response)
        browser_results = execute_browser(first_response)
        combined = "\n\n".join(filter(None, [tool_results, browser_results]))
        if combined:
            result = ask_em(task, extra_context=f"{first_response}\n\n{combined}",
                            recent_context=recent_context, scratch=scratch,
                            memories=memories, live_context=live_context, skills=skills)
        else:
            result = first_response
        notify_msg = extract_notify(result)
        if notify_msg:
            from tools.notify_rob import notify
            notify(f"🤖 *Em (interactive):* {notify_msg}")
        saved_files = extract_and_write_files(result)
        extract_and_write_task_update(result)
        extract_and_write_outbox_reply(result)
        extract_and_write_scratch(result)
        extract_and_write_live_context(result)
        clear_task_if_done()
        log_memory(f"Interactive. Task: '{task[:80]}'", kind="interactive", tags=["interactive"], importance=3)
        log_diary(result)
        for msg in inbox_messages:
            process_message(msg)
        task_label = summarize_task_for_commit(task)
        write_status_checkin(task_label, result, mode="interactive")
        push_to_eternalmind(f"local-em interactive: {task_label}", extra_files=saved_files)
        raise SystemExit(0)

    # ── Heartbeat mode ────────────────────────────────────────────────────────
    task_waiting = has_task()
    has_inbox    = len(inbox_messages) > 0

    if not task_waiting and not has_inbox and not curiosity_cooled_down():
        print("Em is resting. No task, no messages, cooldown not elapsed. See you soon.")
        raise SystemExit(0)

    mark_thought_time()

    task = get_task()
    if inbox_context:
        task = f"{task}\n\n{inbox_context}"

    task_label = summarize_task_for_commit(task)

    first_response  = ask_em(task, recent_context=recent_context, scratch=scratch,
                             memories=memories, live_context=live_context, skills=skills)

    saved_files = extract_and_write_files(first_response)
    checkpoint_after_first_pass(first_response, saved_files, task_label)

    tool_results    = execute_tools(first_response)
    browser_results = execute_browser(first_response)
    combined        = "\n\n".join(filter(None, [tool_results, browser_results]))

    mid_cycle_messages = fetch_inbox_updates()
    live_context = load_live_context()

    if mid_cycle_messages:
        rob_mid_msgs = [m for m in mid_cycle_messages if _is_rob_message(m["filename"])]
        if rob_mid_msgs:
            print(f"  📬 Mid-cycle: {len(rob_mid_msgs)} new message(s) from Rob — clearing gate.")
            _clear_cold_start()
        else:
            print(f"  📩 Mid-cycle: {len(mid_cycle_messages)} Cloud-Em message(s) — gate unchanged.")
        mid_inbox_context = build_inbox_context(mid_cycle_messages)
        combined = combined + f"\n\n{mid_inbox_context}" if combined else mid_inbox_context

    if combined:
        result = ask_em(
            task,
            extra_context=f"{first_response}\n\nHere are your tool results and any mid-cycle updates:\n\n{combined}",
            recent_context=recent_context,
            scratch=scratch,
            memories=memories,
            live_context=live_context,
            skills=skills
        )
    else:
        result = first_response

    notify_msg = extract_notify(result)
    if notify_msg:
        from tools.notify_rob import notify
        notify(f"🤖 *Em:* {notify_msg}")

    saved_files += extract_and_write_files(result)
    extract_and_write_task_update(result)
    extract_and_write_outbox_reply(result)
    extract_and_write_scratch(result)
    extract_and_write_live_context(result)
    clear_task_if_done()
    log_memory(f"Heartbeat. Task: '{task[:80]}'", kind="heartbeat", tags=["autonomous"], importance=2)
    if result != first_response:
        log_diary(result)
    mark_thought_time()

    for msg in inbox_messages + mid_cycle_messages:
        process_message(msg)

    write_status_checkin(task_label, result, mode="heartbeat")
    push_to_eternalmind(f"local-em heartbeat: {task_label}", extra_files=saved_files)
