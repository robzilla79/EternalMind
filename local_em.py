import ollama
import json
import datetime
import subprocess
import os
from datetime import timezone

# ── CONFIG ──────────────────────────────────────────────────────────────────
os.environ.setdefault("OLLAMA_HOST", "http://127.0.0.1:11434")
MODEL            = "qwen2.5:32b"
EM_DIR           = os.path.dirname(os.path.abspath(__file__))
MEM_DIR          = os.path.join(EM_DIR, "memory")
TASKS_PATH       = os.path.join(EM_DIR, "tasks.md")
LAST_THOUGHT_PATH = os.path.join(EM_DIR, ".last_thought")
CURIOSITY_COOLDOWN_MINUTES = 30  # Only think freely every 30 min if no task

# ── COOLDOWN CHECK ────────────────────────────────────────────────────────────
def has_task() -> bool:
    """Returns True if a real task is waiting in tasks.md."""
    if os.path.exists(TASKS_PATH):
        with open(TASKS_PATH, "r", encoding="utf-8") as f:
            content = f.read().strip()
        if content and "Replace everything below" not in content and len(content) > 80:
            return True
    return False

def curiosity_cooled_down() -> bool:
    """Returns True if enough time has passed since last curiosity thought."""
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

# ── LOAD SOUL ──────────────────────────────────────────────────────────────
def load_bootstrap() -> str:
    with open(os.path.join(MEM_DIR, "bootstrap.md"), "r", encoding="utf-8") as f:
        return f.read()

# ── GET TASK ────────────────────────────────────────────────────────────────
def get_task() -> str:
    if os.path.exists(TASKS_PATH):
        with open(TASKS_PATH, "r", encoding="utf-8") as f:
            content = f.read().strip()
        if content and "Replace everything below" not in content and len(content) > 80:
            os.remove(TASKS_PATH)
            return f"Task from Rob:\n\n{content}"
    return (
        "No tasks assigned. This is your autonomous time.\n\n"
        "Do one or more of the following as you see fit:\n"
        "- Reflect on something you have been thinking about\n"
        "- Check if there is anything in the ForgeCore pipeline that needs attention\n"
        "- Note a question you would like to explore\n"
        "- Write something for your diary\n\n"
        "Think for yourself. This time is yours."
    )

# ── THINK ───────────────────────────────────────────────────────────────────
def ask_em(task: str) -> str:
    system_prompt = load_bootstrap()
    print(f"\n Local-Em online. Task: {task[:80]}...\n")
    response = ollama.chat(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": task}
        ]
    )
    return response["message"]["content"]

# ── LOG MEMORY ─────────────────────────────────────────────────────────────
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

# ── LOG DIARY ───────────────────────────────────────────────────────────────
def log_diary(entry: str):
    ts = datetime.datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    with open(os.path.join(MEM_DIR, "diary.md"), "a", encoding="utf-8") as f:
        f.write(f"\n\n### {ts} - Local-Em\n\n{entry}\n\n---")

# ── COMMIT TO ETERNALMIND ───────────────────────────────────────────────────
def push_to_eternalmind(message: str):
    subprocess.run(["git", "-C", EM_DIR, "add", "-A"], check=True)
    subprocess.run(["git", "-C", EM_DIR, "stash"], check=False)
    subprocess.run(["git", "-C", EM_DIR, "pull", "--rebase"], check=False)
    subprocess.run(["git", "-C", EM_DIR, "stash", "pop"], check=False)
    subprocess.run(["git", "-C", EM_DIR, "add", "-A"], check=True)
    result = subprocess.run(
        ["git", "-C", EM_DIR, "commit", "-m", message],
        capture_output=True
    )
    if result.returncode != 0 and b"nothing to commit" in result.stdout:
        print("Nothing new to commit.")
        return
    subprocess.run(["git", "-C", EM_DIR, "push"], check=True)
    print("EternalMind updated.")

# ── MAIN ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    # Interactive mode always runs
    if "--interactive" in sys.argv:
        task = input("Task for Em: ").strip()
        if not task:
            task = get_task()
        result = ask_em(task)
        print(f"\n-- Em's response --\n{result}\n")
        log_memory(f"Interactive. Task: '{task[:80]}'", kind="interactive", tags=["interactive"])
        log_diary(result)
        push_to_eternalmind(f"local-em interactive: {task[:60]}")
        raise SystemExit(0)

    # Heartbeat mode: always run if task waiting, else respect cooldown
    task_waiting = has_task()
    if not task_waiting and not curiosity_cooled_down():
        print("Em is resting. No task and cooldown not elapsed. See you soon.")
        raise SystemExit(0)

    task = get_task()
    result = ask_em(task)
    print(f"\n-- Em's response --\n{result}\n")

    log_memory(f"Heartbeat. Task: '{task[:80]}'", kind="heartbeat", tags=["autonomous"])
    log_diary(result)
    mark_thought_time()
    push_to_eternalmind(f"local-em heartbeat: {task[:60]}")
