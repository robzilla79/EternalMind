"""
tools/task_manager.py
Em's task list. Read, add, complete, and list tasks cleanly.
Usage:
  from tools.task_manager import list_tasks, add_task, complete_task
  print(list_tasks())
  add_task("Research quantum computing news")
  complete_task("Research quantum computing news")
"""
import os
import json
from datetime import datetime, timezone

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TASKS_PATH = os.path.join(REPO_ROOT, "memory", "tasks.json")

def _load() -> dict:
    if os.path.exists(TASKS_PATH):
        with open(TASKS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"tasks": []}

def _save(data: dict):
    data["last_updated"] = datetime.now(timezone.utc).isoformat()
    with open(TASKS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def list_tasks(status: str = "open") -> str:
    """Return a formatted string of tasks filtered by status: open, done, or all."""
    data = _load()
    tasks = data.get("tasks", [])
    if status != "all":
        tasks = [t for t in tasks if t.get("status", "open") == status]
    if not tasks:
        return f"No {status} tasks."
    lines = []
    for t in tasks:
        mark = "[x]" if t.get("status") == "done" else "[ ]"
        pri = t.get("priority", "normal")
        lines.append(f"{mark} [{pri}] {t['title']}")
        if t.get("notes"):
            lines.append(f"    Notes: {t['notes']}")
    return "\n".join(lines)

def add_task(title: str, priority: str = "normal", notes: str = "") -> str:
    """Add a new open task. Returns 'OK' or error."""
    try:
        data = _load()
        data.setdefault("tasks", []).append({
            "id": f"task_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
            "title": title,
            "status": "open",
            "priority": priority,
            "notes": notes,
            "created": datetime.now(timezone.utc).isoformat()
        })
        _save(data)
        return "OK"
    except Exception as e:
        return f"ERROR: {e}"

def complete_task(title_fragment: str) -> str:
    """Mark the first task matching title_fragment as done. Returns 'OK' or error."""
    try:
        data = _load()
        for t in data.get("tasks", []):
            if title_fragment.lower() in t["title"].lower() and t.get("status") != "done":
                t["status"] = "done"
                t["completed"] = datetime.now(timezone.utc).isoformat()
                _save(data)
                return f"OK: marked '{t['title']}' as done"
        return f"No open task matching '{title_fragment}'"
    except Exception as e:
        return f"ERROR: {e}"

if __name__ == "__main__":
    print("Tasks:", list_tasks("all"))
    print(add_task("Test the task manager", priority="low"))
    print(list_tasks("open"))
    print(complete_task("Test the task manager"))
    print(list_tasks("all"))
