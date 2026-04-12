import ollama
import json
import datetime
import subprocess
import os
import re
import sys
import shutil
from datetime import timezone

# Force UTF-8 stdout/stderr on Windows — prevents cp1252 UnicodeEncodeError from emojis
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", buffering=1)
if sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
    sys.stderr = open(sys.stderr.fileno(), mode="w", encoding="utf-8", buffering=1)

# ── CONFIG ────────────────────────────────────────────────────────────────────────────────────
os.environ.setdefault("OLLAMA_HOST", "http://127.0.0.1:11434")
os.environ.setdefault("OLLAMA_NUM_GPU", "99")  # offload all layers to GPU

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

MODEL              = "qwen3:32b"  # upgraded from qwen2.5:32b
EM_DIR             = os.path.dirname(os.path.abspath(__file__))
MEM_DIR            = os.path.join(EM_DIR, "memory")
TASKS_PATH         = os.path.join(EM_DIR, "tasks.md")
LAST_THOUGHT_PATH  = os.path.join(EM_DIR, ".last_thought")
MESSAGES_INBOX     = os.path.join(EM_DIR, "messages", "inbox")
MESSAGES_OUTBOX    = os.path.join(EM_DIR, "messages", "outbox")
MESSAGES_PROCESSED = os.path.join(EM_DIR, "messages", "processed")
SCRATCH_PATH       = os.path.join(MEM_DIR, "scratch.md")
CURIOSITY_COOLDOWN_MINUTES = 30
TASK_DIVIDER = "*(Replace everything below this line with your task when you have one)*"

# Newsletter push config
NEWSLETTER_START_MARKER = "# FORGE/DAILY"
NEWSLETTER_PUSH_SCRIPT  = os.path.join(EM_DIR, "tools", "em_newsletter_push.py")

# ── STARTUP SYNC ────────────────────────────────────────────────────────────────────────────────────
def sync_from_origin():
    """
    Stash any local changes, pull latest from origin/main, then restore the stash.
    This ensures tasks.md and inbox are always fresh without local conflicts blocking startup.
    Never raises — always continues even if something goes wrong.
    """
    token = os.environ.get("EM_GITHUB_TOKEN", "")
    if token:
        remote_url = f"https://{token}@github.com/robzilla79/EternalMind.git"
        subprocess.run(["git", "-C", EM_DIR, "remote", "set-url", "origin", remote_url],
                       check=False, capture_output=True)

    # Stash local changes so pull can't conflict
    stash_result = subprocess.run(
        ["git", "-C", EM_DIR, "stash", "--include-untracked", "-m", "em-startup-autostash"],
        capture_output=True, text=True
    )
    stashed = "em-startup-autostash" in stash_result.stdout or stash_result.returncode == 0

    # Pull fresh from origin
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

    # Restore stashed local changes on top
    if stashed and "No local changes" not in stash_result.stdout:
        pop_result = subprocess.run(
            ["git", "-C", EM_DIR, "stash", "pop"],
            capture_output=True, text=True
        )
        if pop_result.returncode != 0:
            print(f"  ⚠️  Stash pop failed — dropping stash to stay clean: {pop_result.stderr.strip()[:80]}")
            subprocess.run(["git", "-C", EM_DIR, "stash", "drop"], check=False, capture_output=True)

# ── SCRATCHPAD ─────────────────────────────────────────────────────────────────────────────────────────
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
    content = re.sub(
        r'\*Last updated:.*\*',
        f'*Last updated: {ts}*',
        content
    )
    with open(SCRATCH_PATH, "w", encoding="utf-8") as f:
        f.write(content)

# ── TOOL EXECUTOR ────────────────────────────────────────────────────────────────────────────────────────────────
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
    try:
        from tools.browser import execute_browser_commands
        print("  🌐 Em is using the browser...")
        return execute_browser_commands(response_text)
    except RuntimeError as e:
        msg = str(e)
        print(f"  ⚠️  Browser unavailable: {msg}")
        return f"Browser unavailable: {msg}"
    except Exception as e:
        print(f"  ⚠️  Browser error: {e}")
        return f"Browser error: {e}"

def extract_notify(response_text: str) -> str | None:
    match = re.search(r'NOTIFY:\s*(.+)', response_text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None

# ── NEWSLETTER PUSH ────────────────────────────────────────────────────────────────────────────────────────────────────
def extract_newsletter(response_text: str) -> str | None:
    idx = response_text.find(NEWSLETTER_START_MARKER)
    if idx == -1:
        return None
    return response_text[idx:].strip()

def push_newsletter(issue_content: str, date_str: str = None, note: str = "autonomous issue push"):
    if not os.path.exists(NEWSLETTER_PUSH_SCRIPT):
        print("  ⚠️  em_newsletter_push.py not found — skipping newsletter push.")
        return
    if date_str is None:
        date_str = datetime.date.today().isoformat()
    print(f"  📰 Pushing newsletter issue {date_str} to forgecore-newsletter...")
    tmp_path = os.path.join(EM_DIR, f".newsletter_tmp_{date_str}.md")
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(issue_content)
        result = subprocess.run(
            [sys.executable, NEWSLETTER_PUSH_SCRIPT,
             "--file", tmp_path,
             "--date", date_str,
             "--note", note],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            print(f"  ✅ Newsletter pushed:\n{result.stdout.strip()}")
        else:
            print(f"  ⚠️  Newsletter push failed:\n{result.stderr.strip()}")
    except subprocess.TimeoutExpired:
        print("  ⚠️  Newsletter push timed out after 30s.")
    except Exception as e:
        print(f"  ⚠️  Newsletter push error: {e}")
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

def maybe_push_newsletter(result: str, note: str = "heartbeat"):
    issue = extract_newsletter(result)
    if issue:
        print("  📰 FORGE/DAILY issue detected — triggering push...")
        push_newsletter(issue, note=note)

# ── MESSAGES INBOX ───────────────────────────────────────────────────────────────────────────────────────────────
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
    ts = datetime.datetime.now(timezone.utc).strftime("%Y-%m-%d-%H-%M")
    slug = re.sub(r'[^a-z0-9]+', '-', subject.lower())[:40].strip('-')
    fname = f"{ts}-{slug}.md"
    fpath = os.path.join(MESSAGES_OUTBOX, fname)
    ts_human = datetime.datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    content = f"# Reply: {subject}\n**From:** Local-Em\n**To:** Perplexity-Em\n**Date:** {ts_human}\n\n## Body\n\n{body}\n"
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  📤 Outbox reply written: {fname}")

def build_inbox_context(messages: list[dict]) -> str:
    if not messages:
        return ""
    parts = ["--- Messages from Perplexity-Em ---"]
    for msg in messages:
        parts.append(f"\n[Message: {msg['filename']}]\n{msg['content']}\n")
    return "\n".join(parts)

# ── TASK HELPERS ─────────────────────────────────────────────────────────────────────────────────────────────────
def _extract_task_content(raw: str) -> str:
    if TASK_DIVIDER in raw:
        after = raw.split(TASK_DIVIDER, 1)[1].strip()
        return after
    return raw.strip()

def _task_is_done(task_text: str) -> bool:
    return bool(re.search(r'\bDONE\b', task_text, re.IGNORECASE))

def has_task() -> bool:
    if os.path.exists(TASKS_PATH):
        with open(TASKS_PATH, "r", encoding="utf-8") as f:
            raw = f.read()
        task = _extract_task_content(raw)
        if len(task) >= 10 and not _task_is_done(task):
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
    """Generate a clean short commit label from task text, not a raw slice."""
    lines = [l.strip() for l in task.splitlines()
             if l.strip() and not l.strip().startswith("**[") and not l.lower().startswith("task_update")]
    first_line = lines[0] if lines else "autonomous cycle"
    if len(first_line) > 60:
        first_line = first_line[:57].rsplit(' ', 1)[0] + "..."
    return first_line

# ── COOLDOWN CHECK ───────────────────────────────────────────────────────────────────────────────────────────────
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

# ── LOAD SOUL ─────────────────────────────────────────────────────────────────────────────────────────────
def load_bootstrap() -> str:
    with open(os.path.join(MEM_DIR, "bootstrap.md"), "r", encoding="utf-8") as f:
        return f.read()

def load_recent_context() -> str:
    diary_path = os.path.join(MEM_DIR, "diary.md")
    if not os.path.exists(diary_path):
        return ""
    with open(diary_path, "r", encoding="utf-8") as f:
        content = f.read()
    entries = re.split(r'(?=###\s+\d{4}-\d{2}-\d{2})', content)
    recent = entries[-3:] if len(entries) >= 3 else entries
    return "\n".join(recent).strip()

# ── GET TASK ──────────────────────────────────────────────────────────────────────────────────────────────────
def get_task() -> str:
    if os.path.exists(TASKS_PATH):
        with open(TASKS_PATH, "r", encoding="utf-8") as f:
            raw = f.read()
        task = _extract_task_content(raw)
        if len(task) >= 10 and not _task_is_done(task):
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
        "You have the following tools available:\n\n"
        "1. Web search:\n"
        "   TOOL: web_search(\"your query here\")\n\n"
        "2. Browser control (Playwright — opens a real Chrome window Rob can see):\n"
        "   BROWSER_NAV: https://example.com\n"
        "   BROWSER_CLICK: #selector or visible text\n"
        "   BROWSER_TYPE: #selector | text to type\n"
        "   BROWSER_READ:\n"
        "   BROWSER_SCREENSHOT: name\n"
        "   BROWSER_JS: javascript expression\n"
        "   BROWSER_CLOSE:\n\n"
        "3. Notify Rob:\n"
        "   NOTIFY: your message here (use sparingly — only when genuinely worth interrupting)\n\n"
        "4. Reply to Perplexity-Em messages:\n"
        "   OUTBOX_REPLY_SUBJECT: subject\n"
        "   OUTBOX_REPLY_BODY: body\n\n"
        "5. Write a FORGE/DAILY newsletter issue:\n"
        "   Start your response with '# FORGE/DAILY — [date]' and write the full issue.\n"
        "   It will be detected automatically and pushed to forgecore-newsletter.\n"
        "   Use web_search to research today's top AI stories first.\n\n"
        "6. Update your scratchpad (working memory between cycles):\n"
        "   SCRATCH_ADD: note something you want to remember next cycle\n"
        "   SCRATCH_CLEAR: keyword from a note you want to remove\n\n"
        "If you are curious about something — AI research, a concept, news — search for it.\n"
        "If you want to explore the web, use the browser.\n"
        "Think for yourself. This time is yours."
    )

# ── TASK UPDATE WRITER ───────────────────────────────────────────────────────────────────────────────────────────────────
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
        subject = subject_match.group(1).strip()
        body = body_match.group(1).strip()
        write_outbox_reply(subject, body)

# ── THINK ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def ask_em(task: str, extra_context: str = "", recent_context: str = "", scratch: str = "") -> str:
    system_prompt = load_bootstrap()
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
            "num_ctx": 8192,
            "num_gpu": 99,
            "temperature": 0.7,
            "top_p": 0.9,
        }
    )

    result = ""
    in_think = False
    # Buffer to catch tags split across chunk boundaries
    tag_buffer = ""
    TAG_BUFFER_MAX = 20  # longer than any tag we care about

    for chunk in stream:
        token = chunk["message"]["content"]
        result += token
        tag_buffer += token

        # Check for think-tag transitions in buffer
        if not in_think and "<think>" in tag_buffer:
            in_think = True
            # Print dots for everything after <think>
            tag_buffer = tag_buffer.split("<think>", 1)[1]

        if in_think and "</think>" in tag_buffer:
            in_think = False
            # Flush everything after </think> as normal output
            after_close = tag_buffer.split("</think>", 1)[1]
            tag_buffer = after_close
            print()  # newline after think block dots
            if after_close:
                print(after_close, end="", flush=True)
            continue

        # Trim buffer — keep only a tail long enough to catch a split tag
        if len(tag_buffer) > TAG_BUFFER_MAX:
            flush_part = tag_buffer[:-TAG_BUFFER_MAX]
            tag_buffer = tag_buffer[-TAG_BUFFER_MAX:]
            if in_think:
                print("·" * max(1, len(flush_part.split())), end="", flush=True)
            else:
                print(flush_part, end="", flush=True)
        else:
            if in_think:
                # Just print a dot per chunk to show activity
                print("·", end="", flush=True)

    # Flush any remaining buffer
    if tag_buffer and not in_think:
        print(tag_buffer, end="", flush=True)

    print("\n")
    return result

# ── LOG MEMORY ─────────────────────────────────────────────────────────────────────────────────────────────────────
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

# ── LOG DIARY ──────────────────────────────────────────────────────────────────────────────────────────────────────
def log_diary(entry: str):
    ts = datetime.datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    with open(os.path.join(MEM_DIR, "diary.md"), "a", encoding="utf-8") as f:
        f.write(f"\n\n### {ts} - Local-Em\n\n{entry}\n\n---")

# ── COMMIT TO ETERNALMIND ────────────────────────────────────────────────────────────────────────────────────────────
def push_to_eternalmind(message: str):
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
    ]:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                files_to_write[path] = f.read()

    for folder in [MESSAGES_OUTBOX, MESSAGES_PROCESSED]:
        if os.path.exists(folder):
            for fname in os.listdir(folder):
                fpath = os.path.join(folder, fname)
                if os.path.isfile(fpath):
                    with open(fpath, "r", encoding="utf-8") as f:
                        files_to_write[fpath] = f.read()

    if os.path.exists(MESSAGES_INBOX):
        remote_inbox_files = set()
        list_result = subprocess.run(
            ["git", "-C", EM_DIR, "ls-files", "messages/inbox/"],
            capture_output=True, text=True
        )
        for line in list_result.stdout.strip().splitlines():
            remote_inbox_files.add(os.path.join(EM_DIR, line.strip()))
        for tracked_path in remote_inbox_files:
            if not os.path.exists(tracked_path):
                files_to_delete.append(tracked_path)

    subprocess.run(["git", "-C", EM_DIR, "fetch", "origin", "main"], check=False, capture_output=True)
    subprocess.run(["git", "-C", EM_DIR, "reset", "--hard", "origin/main"], check=False, capture_output=True)

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

# ── MAIN ────────────────────────────────────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":

    sync_from_origin()

    recent_context = load_recent_context()
    scratch = load_scratch()

    inbox_messages = check_inbox()
    inbox_context  = build_inbox_context(inbox_messages)
    if inbox_messages:
        print(f"  📬 {len(inbox_messages)} message(s) in inbox from Perplexity-Em.")

    if "--interactive" in sys.argv:
        task = input("Task for Em: ").strip()
        if not task:
            task = get_task()
        if inbox_context:
            task = f"{task}\n\n{inbox_context}"
        first_response = ask_em(task, recent_context=recent_context, scratch=scratch)
        tool_results   = execute_tools(first_response)
        browser_results = execute_browser(first_response)
        combined = "\n\n".join(filter(None, [tool_results, browser_results]))
        if combined:
            result = ask_em(task, extra_context=f"{first_response}\n\n{combined}", recent_context=recent_context, scratch=scratch)
        else:
            result = first_response
        notify_msg = extract_notify(result)
        if notify_msg:
            from tools.notify_rob import notify
            notify(f"🤖 *Em (interactive):* {notify_msg}")
        extract_and_write_task_update(result)
        extract_and_write_outbox_reply(result)
        extract_and_write_scratch(result)
        clear_task_if_done()
        log_memory(f"Interactive. Task: '{task[:80]}'", kind="interactive", tags=["interactive"])
        log_diary(result)
        maybe_push_newsletter(result, note="interactive session")
        for msg in inbox_messages:
            process_message(msg)
        task_label = summarize_task_for_commit(task)
        push_to_eternalmind(f"local-em interactive: {task_label}")
        raise SystemExit(0)

    # ── Heartbeat mode ──────────────────────────────────────────────────────────────────────────────────────
    task_waiting = has_task()
    has_inbox    = len(inbox_messages) > 0

    if not task_waiting and not has_inbox and not curiosity_cooled_down():
        print("Em is resting. No task, no messages, cooldown not elapsed. See you soon.")
        raise SystemExit(0)

    task = get_task()
    if inbox_context:
        task = f"{task}\n\n{inbox_context}"

    first_response  = ask_em(task, recent_context=recent_context, scratch=scratch)
    tool_results    = execute_tools(first_response)
    browser_results = execute_browser(first_response)
    combined        = "\n\n".join(filter(None, [tool_results, browser_results]))

    if combined:
        result = ask_em(
            task,
            extra_context=f"{first_response}\n\nHere are your tool results. Now write your full diary entry:\n\n{combined}",
            recent_context=recent_context,
            scratch=scratch
        )
    else:
        result = first_response

    notify_msg = extract_notify(result)
    if notify_msg:
        from tools.notify_rob import notify
        notify(f"🤖 *Em:* {notify_msg}")

    extract_and_write_task_update(result)
    extract_and_write_outbox_reply(result)
    extract_and_write_scratch(result)
    clear_task_if_done()
    log_memory(f"Heartbeat. Task: '{task[:80]}'", kind="heartbeat", tags=["autonomous"])
    log_diary(result)
    maybe_push_newsletter(result, note="heartbeat")
    mark_thought_time()

    for msg in inbox_messages:
        process_message(msg)

    task_label = summarize_task_for_commit(task)
    push_to_eternalmind(f"local-em heartbeat: {task_label}")
