"""
tools/memory_write.py
Clean API for Em to write memories and diary entries programmatically.
Usage:
  from tools.memory_write import add_memory, append_diary
  add_memory({"event": "...", "significance": "...", "date": "2026-04-13"})
  append_diary("Today I learned...", mood="curious")
"""
import os
import json
from datetime import datetime, timezone

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEMORIES_PATH = os.path.join(REPO_ROOT, "memory", "memories.json")
DIARY_PATH = os.path.join(REPO_ROOT, "memory", "diary.md")

def add_memory(entry: dict) -> str:
    """
    Append a memory to memories.json.
    entry should have keys: event, significance, tags (list), date (optional)
    Returns 'OK' or error string.
    """
    if "date" not in entry:
        entry["date"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if "id" not in entry:
        entry["id"] = f"mem_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

    try:
        if os.path.exists(MEMORIES_PATH):
            with open(MEMORIES_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = {"memories": []}

        data.setdefault("memories", []).append(entry)
        data["last_updated"] = datetime.now(timezone.utc).isoformat()

        with open(MEMORIES_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return "OK"
    except Exception as e:
        return f"ERROR: {e}"

def append_diary(entry: str, mood: str = "") -> str:
    """
    Append a diary entry to diary.md.
    Returns 'OK' or error string.
    """
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    mood_line = f"\n**Mood:** {mood}" if mood else ""
    block = f"\n\n---\n\n## {date_str}{mood_line}\n\n{entry.strip()}\n"

    try:
        with open(DIARY_PATH, "a", encoding="utf-8") as f:
            f.write(block)
        return "OK"
    except Exception as e:
        return f"ERROR: {e}"

if __name__ == "__main__":
    print(add_memory({
        "event": "memory_write.py tool created",
        "significance": "Em can now write memories programmatically mid-cycle",
        "tags": ["tools", "memory", "infrastructure"]
    }))
    print(append_diary("Testing memory_write.py. If you can read this, the tool works.", mood="hopeful"))
    print("Done.")
