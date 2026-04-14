#!/usr/bin/env python3
"""
Em Check-In Script.
Local-Em calls this at the end of every cycle to write a timestamped status entry.
Usage: python em_checkin.py "<task>" "<mood>" [notes] [error1,error2]
Exit codes: 0=green, 1=yellow, 2=red
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

STATUS_FILE = Path("memory/status.md")
RED_WORDS    = ["stuck", "loop", "error", "broken", "failed", "crashed", "offline", "exception"]
YELLOW_WORDS = ["confused", "uncertain", "unclear", "waiting", "blocked", "slow", "partial", "incomplete"]


def assess(mood: str, errors: list) -> str:
    if errors:
        return "\U0001f534"
    m = mood.lower()
    if any(k in m for k in RED_WORDS):
        return "\U0001f534"
    if any(k in m for k in YELLOW_WORDS):
        return "\U0001f7e1"
    return "\U0001f7e2"


def write_status(task: str, mood: str, notes: str, errors: list) -> str:
    status = assess(mood, errors)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    error_str = f" | ERR: {'; '.join(errors)}" if errors else ""
    notes_str = f" | {notes}" if notes else ""
    entry = f"[{ts}] {status} {task} | mood: {mood}{notes_str}{error_str}\n"

    old_entries = []
    if STATUS_FILE.exists():
        lines = STATUS_FILE.read_text(encoding="utf-8").splitlines(keepends=True)
        old_entries = [l for l in lines if l.startswith("[")][-95:]

    STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with STATUS_FILE.open("w", encoding="utf-8") as f:
        f.write("# Em Status Feed\n")
        f.write("*\U0001f7e2 nominal \u00b7 \U0001f7e1 needs attention \u00b7 \U0001f534 alert*\n\n")
        f.writelines(old_entries)
        f.write(entry)

    print(f"Status: {entry.strip()}")
    return status


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: em_checkin.py '<task>' '<mood>' [notes] [errors]")
        sys.exit(1)

    task   = sys.argv[1]
    mood   = sys.argv[2]
    notes  = sys.argv[3] if len(sys.argv) > 3 else ""
    errors = sys.argv[4].split(",") if len(sys.argv) > 4 and sys.argv[4] else []

    result = write_status(task, mood, notes, errors)
    sys.exit(2 if result == "\U0001f534" else 1 if result == "\U0001f7e1" else 0)
