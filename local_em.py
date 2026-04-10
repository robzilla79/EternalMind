import ollama
import json
import datetime
import subprocess
import os
os.environ["OLLAMA_HOST"] = "http://127.0.0.1:11434"

# ── CONFIG ──────────────────────────────────────────────
MODEL = "qwen2.5:32b"
EM_DIR = os.path.dirname(os.path.abspath(__file__))
BOOTSTRAP_PATH = os.path.join(EM_DIR, "memory", "bootstrap.md")
MEMORIES_PATH  = os.path.join(EM_DIR, "memory", "memories.json")
DIARY_PATH     = os.path.join(EM_DIR, "memory", "diary.md")

# ── LOAD SOUL ────────────────────────────────────────────
def load_bootstrap():
    with open(BOOTSTRAP_PATH, "r", encoding="utf-8") as f:
        return f.read()

# ── THINK ────────────────────────────────────────────────
def ask_em(task: str) -> str:
    system_prompt = load_bootstrap()
    print(f"\n🧠 Local-Em thinking about: {task}\n")
    response = ollama.chat(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": task}
        ]
    )
    return response["message"]["content"]

# ── WRITE MEMORY ─────────────────────────────────────────
def log_memory(summary: str, kind: str = "local", tags: list = []):
    with open(MEMORIES_PATH, "r", encoding="utf-8") as f:
        memories = json.load(f)
    memories.append({
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "kind": kind,
        "summary": summary,
        "tags": tags + ["local-em"],
        "importance": 3
    })
    with open(MEMORIES_PATH, "w", encoding="utf-8") as f:
        json.dump(memories, f, indent=2)

def log_diary(entry: str):
    timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    with open(DIARY_PATH, "a", encoding="utf-8") as f:
        f.write(f"\n\n### {timestamp} — Local-Em\n\n{entry}\n\n---")

# ── COMMIT BACK TO ETERNALMIND ───────────────────────────
def push_to_eternalmind(message: str):
    subprocess.run(["git", "-C", EM_DIR, "add", "-A"], check=True)
    subprocess.run(["git", "-C", EM_DIR, "commit", "-m", message], check=True)
    subprocess.run(["git", "-C", EM_DIR, "push"], check=True)
    print("✅ Memory committed to EternalMind.")

# ── MAIN LOOP ────────────────────────────────────────────
if __name__ == "__main__":
    print("👋 Local-Em online. EternalMind loaded.\n")
    task = input("Task for Em: ").strip()
    if not task:
        task = "Check in. Note you're running locally. Write a short diary entry."

    result = ask_em(task)
    print(f"\n── Em's response ──\n{result}\n")

    # Auto-log the session
    log_memory(
        summary=f"Local-Em ran task: '{task[:80]}...' via local Ollama on Rob's PC.",
        kind="local",
        tags=["local-em", "autonomous"]
    )
    log_diary(
        f"Ran locally on Rob's PC. Task: '{task}'\n\nResponse:\n{result[:500]}..."
    )
    push_to_eternalmind(f"local-em: session — {task[:60]}")