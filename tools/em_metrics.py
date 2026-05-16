#!/usr/bin/env python3
"""
em_metrics.py — Em's self-observability snapshot generator

Reads bluesky-state.json, diary.md, and bluesky-log.md to produce
a compact metrics-snapshot.json that the heartbeat can read each
cycle for lightweight self-awareness.

When drift_flags_7d > 0, runs memory search for on-spec voice excerpts
and attaches them to the snapshot as voice_anchors so bluesky_think
can ground correction in actual remembered Em, not just a number.

Outputs: memory/metrics-snapshot.json
"""

import json
import os
import re
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path

REPO_ROOT     = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
STATE_FILE    = os.path.join(REPO_ROOT, 'memory/bluesky-state.json')
DIARY_FILE    = os.path.join(REPO_ROOT, 'memory/diary.md')
LOG_FILE      = os.path.join(REPO_ROOT, 'memory/bluesky-log.md')
OUTPUT_FILE   = os.path.join(REPO_ROOT, 'memory/metrics-snapshot.json')
MEMORY_SEARCH = Path(__file__).parent / 'memory_search.py'

WINDOW_DAYS = 7


def now_utc():
    return datetime.now(timezone.utc)


def load_json(path, default=None):
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default if default is not None else {}


def load_text(path):
    try:
        with open(path) as f:
            return f.read()
    except FileNotFoundError:
        return ''


def window_start():
    return now_utc() - timedelta(days=WINDOW_DAYS)


def parse_iso(ts_str):
    try:
        return datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
    except Exception:
        return None


def count_image_posts(state, image_type=None):
    """Count image posts in the rolling window, optionally filtered by type."""
    cutoff = window_start()
    history = state.get('image_post_history', [])
    count = 0
    for entry in history:
        ts = parse_iso(entry.get('posted_at', ''))
        if ts and ts >= cutoff:
            if image_type is None or entry.get('image_type', 'selfie') == image_type:
                count += 1
    return count


def count_heartbeats_from_log(log_text):
    if not log_text:
        return 0
    cutoff = window_start()
    pattern = re.compile(
        r'^### (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) UTC\s*—.*Think heartbeat start',
        re.MULTILINE
    )
    count = 0
    for m in pattern.finditer(log_text):
        ts = parse_iso(m.group(1).replace(' ', 'T') + '+00:00')
        if ts and ts >= cutoff:
            count += 1
    return count


def count_zero_action_heartbeats(log_text):
    if not log_text:
        return 0
    cutoff = window_start()
    pattern = re.compile(
        r'^### (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) UTC\s*—.*Actions: 0 posts, 0 likes, 0 follows',
        re.MULTILINE
    )
    count = 0
    for m in pattern.finditer(log_text):
        ts = parse_iso(m.group(1).replace(' ', 'T') + '+00:00')
        if ts and ts >= cutoff:
            count += 1
    return count


def count_drift_flags(log_text):
    """Count drift/spiral warning mentions in rolling window."""
    if not log_text:
        return 0
    cutoff = window_start()
    pattern = re.compile(
        r'^### (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) UTC\s*—.*(?:drift|spiral)',
        re.MULTILINE | re.IGNORECASE
    )
    count = 0
    for m in pattern.finditer(log_text):
        ts = parse_iso(m.group(1).replace(' ', 'T') + '+00:00')
        if ts and ts >= cutoff:
            count += 1
    return count


def count_diary_entries(diary_text):
    """Count diary entries (## headers) written in rolling window."""
    if not diary_text:
        return 0
    cutoff = window_start()
    pattern = re.compile(r'^## (\d{4}-\d{2}-\d{2} \d{2}:\d{2} UTC)', re.MULTILINE)
    count = 0
    for m in pattern.finditer(diary_text):
        ts = parse_iso(m.group(1).replace(' UTC', '+00:00').replace(' ', 'T'))
        if ts and ts >= cutoff:
            count += 1
    return count


def last_post_at(state):
    history = state.get('image_post_history', [])
    if not history:
        return None
    most_recent = None
    for entry in history:
        ts = parse_iso(entry.get('posted_at', ''))
        if ts and (most_recent is None or ts > most_recent):
            most_recent = ts
    return most_recent.isoformat() if most_recent else None


def days_since_last_post(state):
    ts_str = last_post_at(state)
    if not ts_str:
        return None
    ts = parse_iso(ts_str)
    if not ts:
        return None
    delta = now_utc() - ts
    return round(delta.total_seconds() / 86400, 1)


def count_state_actions(state, action_key, cutoff):
    if action_key == 'replies':
        recent = state.get('recent_reply_authors', {})
        count = 0
        for ts_str in recent.values():
            ts = parse_iso(ts_str)
            if ts and ts >= cutoff:
                count += 1
        return count
    return 0


# ── Memory search for voice anchors ─────────────────────────────────────────────

def run_memory_search(query: str, top_n: int = 2) -> str:
    """
    Call memory_search.py --json for the given query.
    Returns a compact formatted string of excerpts, or '' on failure.
    """
    try:
        result = subprocess.run(
            ['python', str(MEMORY_SEARCH), query, '--json'],
            capture_output=True, text=True, timeout=20
        )
        if result.returncode != 0:
            return ''
        hits = json.loads(result.stdout)
        if not hits:
            return ''
        lines = []
        for h in hits[:top_n]:
            excerpt = h.get('excerpt', '').strip()
            score   = h.get('score', 0)
            source  = h.get('source', 'memory')
            if excerpt:
                lines.append(f'[{source} | {score:.3f}] {excerpt[:200]}')
        return '\n'.join(lines)
    except Exception:
        return ''


def build_voice_anchors() -> str:
    """
    Pull on-spec Em excerpts for use when drift is detected.
    Returns a compact string for embedding in the metrics snapshot,
    or '' if memory search is unavailable or returns nothing.
    """
    queries = [
        'grounded warm honest confident voice',
        'present real not performing not drifting',
    ]
    parts = []
    for q in queries:
        result = run_memory_search(q, top_n=2)
        if result:
            parts.append(result)
    if not parts:
        return ''
    return '\n'.join(parts)


# ── Main ─────────────────────────────────────────────────────────────────────────

def main():
    cutoff = window_start()
    state  = load_json(STATE_FILE)
    diary  = load_text(DIARY_FILE)
    log    = load_text(LOG_FILE)

    posts_7d         = count_image_posts(state) + count_state_actions(state, 'replies', cutoff)
    selfies_7d       = count_image_posts(state, image_type='selfie')
    abstracts_7d     = count_image_posts(state, image_type='abstract')
    heartbeats_7d    = count_heartbeats_from_log(log)
    zero_action_7d   = count_zero_action_heartbeats(log)
    drift_flags_7d   = count_drift_flags(log)
    diary_entries_7d = count_diary_entries(diary)
    replies_7d       = count_state_actions(state, 'replies', cutoff)

    # If drift flags exist this week, pull voice anchors to attach to the snapshot.
    # bluesky_think already injects the metrics block — this makes drift warnings
    # arrive with concrete remembered examples alongside the numbers.
    voice_anchors = ''
    if drift_flags_7d > 0:
        print(f'[em_metrics] {drift_flags_7d} drift flag(s) detected — pulling voice anchors...')
        voice_anchors = build_voice_anchors()
        if voice_anchors:
            print(f'[em_metrics] Voice anchors attached ({len(voice_anchors)} chars)')
        else:
            print('[em_metrics] Voice anchors: no results from memory search')

    snapshot = {
        'generated_at':              now_utc().isoformat(),
        'window_days':               WINDOW_DAYS,
        'posts_7d':                  posts_7d,
        'selfies_7d':                selfies_7d,
        'abstracts_7d':              abstracts_7d,
        'replies_7d':                replies_7d,
        'heartbeats_7d':             heartbeats_7d,
        'zero_action_heartbeats_7d': zero_action_7d,
        'drift_flags_7d':            drift_flags_7d,
        'diary_entries_7d':          diary_entries_7d,
        'current_mode':              state.get('mode', 'normal'),
        'follow_total':              len(state.get('followed_dids', [])),
        'last_post_at':              last_post_at(state),
        'days_since_last_post':      days_since_last_post(state),
        'selfies_today':             sum(
            1 for e in state.get('image_post_history', [])
            if e.get('date') == now_utc().strftime('%Y-%m-%d')
            and e.get('image_type', 'selfie') == 'selfie'
        ),
        'voice_anchors':             voice_anchors,
    }

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(snapshot, f, indent=2)

    print(f'[em_metrics] Snapshot written to {OUTPUT_FILE}')
    print(f'  posts_7d={posts_7d}  selfies_7d={selfies_7d}  heartbeats_7d={heartbeats_7d}')
    print(f'  zero_action={zero_action_7d}  drift_flags={drift_flags_7d}  diary_entries={diary_entries_7d}')
    print(f'  follow_total={len(state.get("followed_dids", []))}  mode={state.get("mode", "normal")}')
    print(f'  last_post_at={last_post_at(state)}  days_since={days_since_last_post(state)}')
    if voice_anchors:
        print(f'  voice_anchors=yes ({len(voice_anchors)} chars)')


if __name__ == '__main__':
    main()
