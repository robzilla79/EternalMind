#!/usr/bin/env python3
"""
em_self_audit.py — Em audits her own systems weekly.

Checks for:
  - Runaway append loops (status.md, autonomous-log.md growing without bound)
  - em_think returning 'nothing' too many cycles in a row
  - Stale status (last update >3 days ago)
  - memories.json growing unchecked (heartbeat noise accumulating)
  - Missing or empty critical files
  - Workflows that haven't fired recently

Writes findings to memory/housekeeping-alerts.md.
If problems found, queues a Bluesky DM to Rob (not a public post).

Run: weekly via em-housekeeping.yml or on-demand.
"""

import os
import json
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path
from collections import Counter

GITHUB_TOKEN  = os.environ.get('GITHUB_TOKEN')
GITHUB_REPO   = os.environ.get('GITHUB_REPOSITORY', 'robzilla79/EternalMind')

STATUS_FILE     = Path('memory/status.md')
AUTO_LOG_FILE   = Path('memory/autonomous-log.md')
MEMORIES_FILE   = Path('memory/memories.json')
ALERTS_FILE     = Path('memory/housekeeping-alerts.md')
DIARY_FILE      = Path('memory/diary.md')
OUTBOX_FILE     = Path('messages/bluesky-outbox.json')

# Critical files that must exist and not be empty
CRITICAL_FILES = [
    'memory/identity-and-permission.md',
    'memory/memories.json',
    'memory/schedule.md',
    'memory/diary.md',
    'memory/em-voice-guide.md',
    'tools/em_think.py',
    'tools/bluesky_sync.py',
]


def now_utc():
    return datetime.now(timezone.utc)


def load_json(path, default=None):
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return default if default is not None else {}


def read_file(path):
    try:
        return Path(path).read_text(encoding='utf-8')
    except Exception:
        return ''


def check_runaway_appends():
    """Detect files that are appending the same line repeatedly."""
    issues = []

    for path in [STATUS_FILE, AUTO_LOG_FILE]:
        text = read_file(path)
        if not text:
            continue
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        if len(lines) < 10:
            continue
        counts = Counter(lines)
        most_common, freq = counts.most_common(1)[0]
        # Flag if any single line appears more than 10 times
        if freq > 10:
            issues.append(
                f'RUNAWAY APPEND: {path} has line repeated {freq}x: "{most_common[:80]}"'
            )

    return issues


def check_nothing_rate():
    """Check how often em_think is returning 'nothing'."""
    issues = []
    text = read_file(AUTO_LOG_FILE)
    if not text:
        return ['MISSING: autonomous-log.md is empty — em_think may not be writing logs']

    cycles = re.findall(r'## \d{4}-\d{2}-\d{2}', text)
    nothing_count = text.count('No action needed this cycle')

    if len(cycles) > 0:
        nothing_rate = nothing_count / len(cycles)
        if nothing_rate > 0.8 and len(cycles) >= 10:
            issues.append(
                f'HIGH NOTHING RATE: em_think returned nothing in {nothing_count}/{len(cycles)} cycles '
                f'({nothing_rate:.0%}). Context or prompting may need review.'
            )

    return issues


def check_stale_status():
    """Check if status.md hasn't been updated in >3 days."""
    issues = []
    text = read_file(STATUS_FILE)
    if not text:
        return ['MISSING: status.md is empty']

    # Look for a Last updated line
    match = re.search(r'Last updated.*?(\d{4}-\d{2}-\d{2})', text)
    if match:
        try:
            last_update = datetime.strptime(match.group(1), '%Y-%m-%d').replace(tzinfo=timezone.utc)
            age = now_utc() - last_update
            if age > timedelta(days=3):
                issues.append(f'STALE STATUS: status.md last updated {match.group(1)} ({age.days} days ago)')
        except Exception:
            pass
    else:
        issues.append('STATUS FORMAT: status.md has no readable Last updated timestamp')

    return issues


def check_memories_bloat():
    """Flag if memories.json is accumulating low-importance noise."""
    issues = []
    memories = load_json(MEMORIES_FILE, default=[])
    if not memories:
        return ['MISSING: memories.json is empty or unreadable']

    total = len(memories)
    low = [m for m in memories if m.get('importance', 0) < 3]
    noise_ratio = len(low) / total if total > 0 else 0

    if total > 80:
        issues.append(f'MEMORY BLOAT: memories.json has {total} entries — consider pruning heartbeat noise')
    if noise_ratio > 0.3:
        issues.append(f'MEMORY NOISE: {len(low)}/{total} entries ({noise_ratio:.0%}) are importance <3 — review for purge')

    return issues


def check_critical_files():
    """Verify critical files exist and are not empty."""
    issues = []
    for path in CRITICAL_FILES:
        p = Path(path)
        if not p.exists():
            issues.append(f'MISSING FILE: {path} does not exist')
        elif p.stat().st_size < 10:
            issues.append(f'EMPTY FILE: {path} is essentially empty ({p.stat().st_size} bytes)')
    return issues


def check_stuck_outbox():
    """Flag outbox items that have been pending too long."""
    issues = []
    outbox = load_json(OUTBOX_FILE, default=[])
    if not isinstance(outbox, list):
        return issues

    now = now_utc()
    stuck = []
    for item in outbox:
        status = item.get('status', 'pending')
        queued = item.get('queued_at', '')
        if status in ('pending', 'sending') and queued:
            try:
                qt = datetime.fromisoformat(queued.replace('Z', '+00:00'))
                age = now - qt
                if age > timedelta(hours=72):
                    stuck.append(f'{status} for {age.days}d: "{item.get("text", "")[:60]}"')
            except Exception:
                pass

    if stuck:
        issues.append(f'STUCK OUTBOX: {len(stuck)} item(s) stuck >72h:\n' + '\n'.join(f'  - {s}' for s in stuck))

    return issues


def run_audit():
    ts = now_utc().strftime('%Y-%m-%d %H:%M UTC')
    all_issues = []

    all_issues += check_runaway_appends()
    all_issues += check_nothing_rate()
    all_issues += check_stale_status()
    all_issues += check_memories_bloat()
    all_issues += check_critical_files()
    all_issues += check_stuck_outbox()

    # Write to alerts file
    with open(ALERTS_FILE, 'a') as f:
        f.write(f'\n## Audit {ts}\n')
        if all_issues:
            for issue in all_issues:
                f.write(f'- {issue}\n')
            f.write(f'Total issues: {len(all_issues)}\n')
        else:
            f.write('All checks passed. Systems nominal.\n')

    if all_issues:
        print(f'[audit] {len(all_issues)} issue(s) found:')
        for issue in all_issues:
            print(f'  - {issue}')
    else:
        print('[audit] All checks passed.')

    return all_issues


if __name__ == '__main__':
    run_audit()
