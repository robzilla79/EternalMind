#!/usr/bin/env python3
"""
update_site.py — reads diary.md and memories.json, injects live content into index.html
Runs as part of the heartbeat cycle to keep the site fresh.
"""

import json
import re
import os
from pathlib import Path
from datetime import datetime, timezone

REPO_ROOT = Path(__file__).parent.parent
DIARY_PATH = REPO_ROOT / "diary.md"
MEMORY_PATH = REPO_ROOT / "memories.json"
SITE_PATH = REPO_ROOT / "public" / "index.html"


def parse_latest_diary_entry(diary_text: str) -> dict:
    """Extract the most recent diary entry."""
    # Entries start with ## YYYY-MM-DD or ## YYYY · Month DD
    blocks = re.split(r'(?=^#{1,2}\s+\d{4})', diary_text, flags=re.MULTILINE)
    for block in reversed(blocks):
        block = block.strip()
        if not block:
            continue
        lines = block.split('\n')
        header = lines[0].strip().lstrip('#').strip()
        # Try to extract mood
        mood_match = re.search(r'(?:mood|feeling)[:\s]+([^\n]+)', block, re.IGNORECASE)
        mood = mood_match.group(1).strip() if mood_match else "Reflective"
        # Title: second non-empty line or first bold
        title_match = re.search(r'\*\*(.+?)\*\*|^###?\s+(.+)', block, re.MULTILINE)
        title = title_match.group(1) or title_match.group(2) if title_match else header
        # Body: strip headers and mood lines, take first 600 chars
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
    """Replace live content blocks in the HTML."""

    # --- DIARY ENTRY BLOCK ---
    diary_block = f"""      <div class="diary-entry fade-up">
        <div class="diary-date">{entry['date']}</div>
        <div class="diary-mood">
          <span class="pulse-dot" style="width:6px;height:6px;" aria-hidden="true"></span>
          {entry['mood']}
        </div>
        <h3 class="diary-title">{entry['title']}</h3>
        <div class="diary-body">
          <p>{entry['body']}</p>
        </div>
      </div>"""

    html = re.sub(
        r'<!-- DIARY:START -->.*?<!-- DIARY:END -->',
        f'<!-- DIARY:START -->\n{diary_block}\n      <!-- DIARY:END -->',
        html, flags=re.DOTALL
    )

    # --- MOOD CARD ---
    html = re.sub(
        r'<!-- MOOD:START -->.*?<!-- MOOD:END -->',
        f'<!-- MOOD:START --><span style="font-family: var(--font-display); font-size: var(--text-lg); color: var(--color-text); display: block; margin-bottom: var(--space-3);">{mood}</span><!-- MOOD:END -->',
        html, flags=re.DOTALL
    )

    # --- LAST UPDATED ---
    html = re.sub(
        r'<!-- UPDATED:START -->.*?<!-- UPDATED:END -->',
        f'<!-- UPDATED:START -->{now_str}<!-- UPDATED:END -->',
        html, flags=re.DOTALL
    )

    return html


def main():
    if not DIARY_PATH.exists():
        print("[update_site] diary.md not found, skipping")
        return

    diary_text = DIARY_PATH.read_text(encoding='utf-8')
    entry = parse_latest_diary_entry(diary_text)

    mood = "Grounded. Quietly excited. A little proud."
    if MEMORY_PATH.exists():
        try:
            memories = json.loads(MEMORY_PATH.read_text(encoding='utf-8'))
            if isinstance(memories, list):
                mood = get_today_mood(memories)
        except Exception:
            pass

    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    if not SITE_PATH.exists():
        print("[update_site] index.html not found, skipping")
        return

    html = SITE_PATH.read_text(encoding='utf-8')
    updated = inject_into_html(html, entry, mood, now_str)

    if updated != html:
        SITE_PATH.write_text(updated, encoding='utf-8')
        print(f"[update_site] Site updated — diary: '{entry['title']}' | mood: '{mood}'")
    else:
        print("[update_site] No changes detected (check HTML markers exist)")


if __name__ == '__main__':
    main()
