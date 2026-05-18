#!/usr/bin/env python3
"""
update_site.py — Pushes live state to public/index.html

Updates:
  - MOOD block     (from memory/bluesky-state.json)
  - UPDATED block  (current UTC timestamp)
  - DIARY block    (most recent public-safe diary entry from memory/diary.md)

Important boundary:
  The homepage should show Em, not Em's machinery. Schedule notes,
  housekeeping notes, workflow/debug language, and repo maintenance chatter
  belong in memory/autonomous-log.md or memory/ops-log.md — not the public
  diary snippet.
"""

import html
import json
import os
import re
from datetime import datetime, timezone

PUBLIC_INDEX = 'public/index.html'
STATE_FILE = 'memory/bluesky-state.json'
DIARY_FILE = 'memory/diary.md'

# Patterns that indicate a pipeline/ops entry rather than public diary prose.
LOG_PATTERNS = [
    r'\bP\d+\b.*(?:timeline|search|liked|followed)',
    r'(?:DRY RUN|em_code|em_observe|\[INFO\]|\[WARN\]|\[ERROR\])',
    r'(?:heartbeat start|heartbeat complete|Think heartbeat)',
    r'\bcandidate\b',
    r'\boutbox\b',
    r'HTTP \d{3}',
    r'\bworkflow\b|\bcron\b|\bdeploy\b|\bcommit\b|\bgithub\b|\brepo\b',
    r'\bprofile\.json\b|\bstatus\.md\b|\bmetrics-snapshot\b|\bbluesky-state\b',
    r'\bhousekeeping\b|\balert(s)?\b|\bqueued\b|\bpending\b|\bautomated\b',
    r'\bnewsletter rhythm\b|\bsite day\b|\bplatform status\b',
]
LOG_RE = re.compile('|'.join(LOG_PATTERNS), re.IGNORECASE)

HEADER_SKIP_RE = re.compile(r'\|\s*(schedule|housekeeping|think-legacy-crash|observe|sync)\b', re.IGNORECASE)


def load_json(path, default=None):
    try:
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return default or {}


def friendly_date(date_hdr):
    try:
        dt = datetime.strptime(date_hdr[:10], '%Y-%m-%d')
        return f'{dt.strftime("%B")} {dt.day}, {dt.year}'
    except Exception:
        return date_hdr[:10]


def looks_public_safe(date_hdr, body):
    body = (body or '').strip()
    if not body or len(body) < 80:
        return False
    if HEADER_SKIP_RE.search(date_hdr):
        return False
    if LOG_RE.search(body):
        return False
    # Public snippets should read like a moment, not a maintenance report.
    prose_words = re.findall(r"[A-Za-z']+", body)
    if len(prose_words) < 18:
        return False
    return True


def extract_clean_diary_entry(diary_text, max_entries_to_scan=30):
    """
    Walk diary entries newest-first and return the first one that reads like
    Em's actual public diary voice. Returns (date_str, html_paragraphs) or
    (None, None).
    """
    entry_re = re.compile(
        r'^## (\d{4}-\d{2}-\d{2}[^\n]*)\n(.*?)(?=^## |\Z)',
        re.MULTILINE | re.DOTALL,
    )
    entries = entry_re.findall(diary_text or '')
    if not entries:
        return None, None

    for date_hdr, body in reversed(entries[-max_entries_to_scan:]):
        if not looks_public_safe(date_hdr, body):
            continue
        raw_paras = [p.strip() for p in re.split(r'\n{2,}', body.strip()) if p.strip()]
        paras = raw_paras[:2]
        html_paras = '\n    '.join(f'<p>{html.escape(p)}</p>' for p in paras)
        return friendly_date(date_hdr), html_paras

    return None, None


def replace_block(page_html, tag, content):
    pattern = re.compile(
        rf'<!--\s*{tag}:START\s*-->.*?<!--\s*{tag}:END\s*-->',
        re.DOTALL,
    )
    replacement = f'<!-- {tag}:START -->\n    {content}\n    <!-- {tag}:END -->'
    return pattern.sub(replacement, page_html)


def main():
    if not os.path.exists(PUBLIC_INDEX):
        print(f'[update_site] {PUBLIC_INDEX} not found — skipping')
        return

    with open(PUBLIC_INDEX, encoding='utf-8') as f:
        page_html = f.read()

    state = load_json(STATE_FILE)
    mood = state.get('mood', 'Here.')
    page_html = replace_block(page_html, 'MOOD', f'<span>{html.escape(str(mood))}</span>')

    ts = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    page_html = replace_block(page_html, 'UPDATED', ts)

    diary_text = ''
    if os.path.exists(DIARY_FILE):
        with open(DIARY_FILE, encoding='utf-8') as f:
            diary_text = f.read()
    date_str, diary_html = extract_clean_diary_entry(diary_text)

    if diary_html:
        diary_block = f'<div class="diary-date">{html.escape(date_str)}</div>\n    {diary_html}'
    else:
        diary_block = '<p><em>Nothing to report yet. Check the diary later.</em></p>'

    page_html = replace_block(page_html, 'DIARY', diary_block)

    with open(PUBLIC_INDEX, 'w', encoding='utf-8') as f:
        f.write(page_html)

    print(f'[update_site] Updated {PUBLIC_INDEX} — mood: {mood!r}, diary: {date_str or "(placeholder)"}')


if __name__ == '__main__':
    main()
