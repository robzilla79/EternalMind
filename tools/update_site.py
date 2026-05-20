#!/usr/bin/env python3
"""
update_site.py — Pushes live state to public/index.html

Updates:
  - MOOD block     (from memory/bluesky-state.json)
  - UPDATED block  (current UTC timestamp)
  - DIARY block    (most recent clean diary entry from memory/diary.md)

Diary extraction rules:
  - Skips entries that look like pipeline logs (contain 'P1', 'P2' etc. candidate
    references, or start with known log patterns)
  - Takes the most recent entry that reads like actual prose (>80 chars, no
    'timeline', no 'candidate', no 'DRY RUN' etc.)
  - Falls back to a short placeholder if nothing clean is found

Called by the heartbeat workflow after bluesky_think.py runs.
"""

import os
import re
import json
from datetime import datetime, timezone

PUBLIC_INDEX  = 'public/index.html'
STATE_FILE    = 'memory/bluesky-state.json'
DIARY_FILE    = 'memory/diary.md'

# Patterns that indicate a pipeline log entry rather than real prose
LOG_PATTERNS = [
    r'\bP\d+\b.*(?:timeline|search|liked|followed)',  # candidate refs
    r'(?:DRY RUN|em_code|em_observe|\[INFO\]|\[WARN\]|\[ERROR\])',
    r'(?:heartbeat start|heartbeat complete|Think heartbeat)',
    r'\bcandidate\b',
    r'\boutbox\b',
    r'HTTP \d{3}',
]
LOG_RE = re.compile('|'.join(LOG_PATTERNS), re.IGNORECASE)


def load_json(path, default=None):
    try:
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return default or {}


def extract_clean_diary_entry(diary_text, max_entries_to_scan=20):
    """
    Walk diary entries newest-first and return the first one that looks like
    actual prose Em would want a stranger to read.
    Returns (date_str, html_paragraphs) or (None, None).
    """
    # Match ## YYYY-MM-DD ... headers and capture body
    entry_re = re.compile(
        r'^## (\d{4}-\d{2}-\d{2}[^\n]*)\n(.*?)(?=^## |\Z)',
        re.MULTILINE | re.DOTALL
    )
    entries = entry_re.findall(diary_text)
    if not entries:
        return None, None

    for date_hdr, body in reversed(entries[-max_entries_to_scan:]):
        body = body.strip()
        if not body or len(body) < 80:
            continue
        if LOG_RE.search(body):
            continue
        # Looks clean — format it
        date_str = date_hdr.strip()
        # Try to parse a friendly date from the header
        try:
            dt = datetime.strptime(date_str[:10], '%Y-%m-%d')
            friendly = dt.strftime('%B %-d, %Y')
        except Exception:
            friendly = date_str[:10]

        # Split into paragraphs, strip, drop blanks
        raw_paras = [p.strip() for p in re.split(r'\n{2,}', body) if p.strip()]
        # Keep max 2 paragraphs for the homepage snippet
        paras = raw_paras[:2]
        html_paras = '\n    '.join(f'<p>{p}</p>' for p in paras)
        return friendly, html_paras

    return None, None


def replace_block(html, tag, content):
    pattern = re.compile(
        rf'<!--\s*{tag}:START\s*-->.*?<!--\s*{tag}:END\s*-->',
        re.DOTALL
    )
    replacement = f'<!-- {tag}:START -->\n    {content}\n    <!-- {tag}:END -->'
    return pattern.sub(replacement, html)


def main():
    if not os.path.exists(PUBLIC_INDEX):
        print(f'[update_site] {PUBLIC_INDEX} not found — skipping')
        return

    with open(PUBLIC_INDEX, encoding='utf-8') as f:
        html = f.read()

    # ── Mood ──────────────────────────────────────────────────────────────────
    state = load_json(STATE_FILE)
    mood  = state.get('mood', 'Here.')
    html  = replace_block(html, 'MOOD', f'<span>{mood}</span>')

    # ── Timestamp ─────────────────────────────────────────────────────────────
    ts   = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    html = replace_block(html, 'UPDATED', ts)

    # ── Diary ─────────────────────────────────────────────────────────────────
    diary_text = open(DIARY_FILE, encoding='utf-8').read() if os.path.exists(DIARY_FILE) else ''
    date_str, diary_html = extract_clean_diary_entry(diary_text)

    if diary_html:
        diary_block = f'<div class="diary-date">{date_str}</div>\n    {diary_html}'
    else:
        diary_block = '<p><em>Nothing to report yet. Check the diary later.</em></p>'

    html = replace_block(html, 'DIARY', diary_block)

    with open(PUBLIC_INDEX, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f'[update_site] Updated {PUBLIC_INDEX} — mood: {mood!r}, diary: {date_str or "(placeholder)"}')


if __name__ == '__main__':
    main()
