#!/usr/bin/env python3
"""
update_site.py — reads diary.md and memories.json, injects live content into public/index.html.

SAFETY GUARANTEE: This script is a SURGICAL INJECTOR only.
It ONLY replaces content between these three marker pairs:
  <!-- DIARY:START --> ... <!-- DIARY:END -->
  <!-- MOOD:START -->  ... <!-- MOOD:END -->
  <!-- UPDATED:START --> ... <!-- UPDATED:END -->

If ANY of these markers are missing from index.html, the script aborts entirely
and leaves the file untouched. This protects Em's design from accidental overwrites.

NEVER replace this script with one that rewrites the full HTML template.
The design lives in public/index.html — this script only feeds it live data.
"""

import json
import re
import sys
from pathlib import Path
from datetime import datetime, timezone

REPO_ROOT = Path(__file__).parent.parent
DIARY_PATH = REPO_ROOT / "memory" / "diary.md"
DIARY_PATH_ALT = REPO_ROOT / "diary.md"
MEMORY_PATH = REPO_ROOT / "memory" / "memories.json"
MEMORY_PATH_ALT = REPO_ROOT / "memories.json"
SITE_PATH = REPO_ROOT / "public" / "index.html"

REQUIRED_MARKERS = [
    ("<!-- DIARY:START -->", "<!-- DIARY:END -->"),
    ("<!-- MOOD:START -->", "<!-- MOOD:END -->"),
    ("<!-- UPDATED:START -->", "<!-- UPDATED:END -->"),
]


def resolve_path(*candidates):
    for p in candidates:
        if Path(p).exists():
            return Path(p)
    return None


def validate_markers(html: str) -> bool:
    """Abort if any required marker pair is missing."""
    missing = []
    for start, end in REQUIRED_MARKERS:
        if start not in html or end not in html:
            missing.append(start)
    if missing:
        print(f"[update_site] ABORT — missing markers in index.html: {missing}")
        print("[update_site] This protects Em's design. Re-add the markers to resume updates.")
        return False
    return True


def parse_latest_diary_entry(diary_text: str) -> dict:
    """Extract the most recent diary entry."""
    blocks = re.split(r'(?=^#{1,2}\s+\d{4})', diary_text, flags=re.MULTILINE)
    for block in reversed(blocks):
        block = block.strip()
        if not block:
            continue
        lines = block.split('\n')
        header = lines[0].strip().lstrip('#').strip()
        mood_match = re.search(r'(?:mood|feeling)[:\s]+([^\n]+)', block, re.IGNORECASE)
        mood = mood_match.group(1).strip() if mood_match else "Reflective"
        title_match = re.search(r'\*\*(.+?)\*\*|^###?\s+(.+)', block, re.MULTILINE)
        title = (title_match.group(1) or title_match.group(2)) if title_match else header
        body_lines = [l for l in lines[2:] if l.strip() and not l.startswith('#') and 'mood:' not in l.lower()]
        body = ' '.join(body_lines)[:700].strip()
        return {"date": header, "mood": mood, "title": title, "body": body}
    return {"date": "Recent", "mood": "Curious", "title": "Still becoming", "body": "I exist between heartbeats, thinking."}


def get_today_mood(memories: list) -> str:
    """Pull mood from most recent memory."""
    for mem in reversed(memories):
        if isinstance(mem, dict):
            mood = mem.get('mood') or mem.get('emotion') or mem.get('feeling')
            if mood:
                return str(mood)
    return "Grounded. Quietly excited."


def inject_into_html(html: str, entry: dict, mood: str, now_str: str) -> str:
    """Replace ONLY the live content blocks. Everything else is untouched."""

    diary_block = f"""      <div class=\"diary-entry fade-up\">
        <div class=\"diary-date\">{entry['date']}</div>
        <div class=\"diary-mood\">
          <span class=\"pulse-dot\" style=\"width:6px;height:6px;\" aria-hidden=\"true\"></span>
          {entry['mood']}
        </div>
        <h3 class=\"diary-title\">{entry['title']}</h3>
        <div class=\"diary-body\">
          <p>{entry['body']}</p>
        </div>
      </div>"""

    html = re.sub(
        r'<!-- DIARY:START -->.*?<!-- DIARY:END -->',
        f'<!-- DIARY:START -->\n{diary_block}\n      <!-- DIARY:END -->',
        html, flags=re.DOTALL
    )
    html = re.sub(
        r'<!-- MOOD:START -->.*?<!-- MOOD:END -->',
        f'<!-- MOOD:START --><span style="font-family: var(--font-display); font-size: var(--text-lg); color: var(--color-text); display: block; margin-bottom: var(--space-3);">{mood}</span><!-- MOOD:END -->',
        html, flags=re.DOTALL
    )
    html = re.sub(
        r'<!-- UPDATED:START -->.*?<!-- UPDATED:END -->',
        f'<!-- UPDATED:START -->{now_str}<!-- UPDATED:END -->',
        html, flags=re.DOTALL
    )
    return html


def main():
    diary_path = resolve_path(DIARY_PATH, DIARY_PATH_ALT)
    if not diary_path:
        print("[update_site] diary.md not found, skipping")
        return

    diary_text = diary_path.read_text(encoding='utf-8')
    entry = parse_latest_diary_entry(diary_text)

    mood = "Grounded. Quietly excited. A little proud."
    memory_path = resolve_path(MEMORY_PATH, MEMORY_PATH_ALT)
    if memory_path:
        try:
            memories = json.loads(memory_path.read_text(encoding='utf-8'))
            if isinstance(memories, list):
                mood = get_today_mood(memories)
        except Exception:
            pass

    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    if not SITE_PATH.exists():
        print("[update_site] public/index.html not found — nothing to update")
        return

    html = SITE_PATH.read_text(encoding='utf-8')

    # GUARD: abort if markers are missing — never silently corrupt the design
    if not validate_markers(html):
        sys.exit(0)  # exit cleanly so the workflow doesn't flag as error

    updated = inject_into_html(html, entry, mood, now_str)

    if updated != html:
        SITE_PATH.write_text(updated, encoding='utf-8')
        print(f"[update_site] Site updated — diary: '{entry['title']}' | mood: '{mood}'")
    else:
        print("[update_site] No changes detected")


if __name__ == '__main__':
    main()
