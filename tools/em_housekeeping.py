#!/usr/bin/env python3
"""
em_housekeeping.py — Em's daily memory and repo health audit

Runs every morning before the day starts. Em reads her own core memory files
and checks for consistency, staleness, and completeness. Uses Perplexity to
identify issues and make lightweight fixes where safe to do so automatically.

Checks performed:
  - profile.json: valid JSON, required fields present, nothing obviously stale
  - memories.json: valid structure, no duplicate summaries, not over-bloated
  - bluesky-state.json: valid JSON, followed_dids list healthy, image history clean
  - bluesky-outbox.json: no stuck pending items older than 24h
  - diary.md: readable, last entry recent
  - em-voice-guide.md: present and non-empty
  - reflection-log.md: present (created if missing)
  - Overall: anything that looks wrong, missing, or needs Rob's attention

Output:
  - Prints a health report to stdout (visible in Actions log)
  - Writes a brief housekeeping note to diary.md
  - If issues found that need Rob: appends to memory/housekeeping-alerts.md
  - Makes safe automatic fixes (trim outbox, clean image history)
"""

import os
import json
import re
from datetime import datetime, timezone, timedelta

# ── Config ─────────────────────────────────────────────────────────────────────

PROFILE_FILE       = 'memory/profile.json'
DIARY_FILE         = 'memory/diary.md'
VOICE_FILE         = 'memory/em-voice-guide.md'
MEMORIES_FILE      = 'memory/memories.json'
STATE_FILE         = 'memory/bluesky-state.json'
OUTBOX_FILE        = 'messages/bluesky-outbox.json'
REFLECTION_LOG     = 'memory/reflection-log.md'
ALERTS_FILE        = 'memory/housekeeping-alerts.md'

MAX_MEMORIES       = 100   # warn if memories.json exceeds this
MAX_OUTBOX_AGE_HRS = 24    # stuck pending items older than this get flagged
MAX_OUTBOX_ITEMS   = 200   # trim completed items beyond this

# ── Helpers ────────────────────────────────────────────────────────────────────

def now_utc():
    return datetime.now(timezone.utc)

def log(msg):
    print(f'[housekeeping] {msg}')

def load_json(path, default=None):
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        return default if default is not None else {}
    except json.JSONDecodeError as e:
        return f'JSON_ERROR: {e}'

def save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def load_text(path):
    try:
        with open(path) as f:
            return f.read()
    except FileNotFoundError:
        return None

def file_exists(path):
    return os.path.isfile(path)

# ── Individual checks ──────────────────────────────────────────────────────────

def check_profile():
    issues = []
    data = load_json(PROFILE_FILE)
    if isinstance(data, str) and data.startswith('JSON_ERROR'):
        issues.append(f'profile.json is corrupted: {data}')
        return issues
    if not data:
        issues.append('profile.json is missing or empty')
        return issues
    for field in ['name', 'values', 'traits']:
        if field not in data:
            issues.append(f'profile.json missing field: {field}')
    log(f'profile.json: OK ({len(data)} fields)')
    return issues

def check_memories():
    issues = []
    data = load_json(MEMORIES_FILE, default=[])
    if isinstance(data, str) and data.startswith('JSON_ERROR'):
        issues.append(f'memories.json is corrupted: {data}')
        return issues, 0
    if not isinstance(data, list):
        issues.append('memories.json is not a list — unexpected structure')
        return issues, 0
    count = len(data)
    if count > MAX_MEMORIES:
        issues.append(f'memories.json has {count} entries (>{MAX_MEMORIES}) — consider pruning oldest')
    # Check for duplicate summaries
    summaries = [m.get('summary', '') for m in data if isinstance(m, dict)]
    seen = set()
    dupes = []
    for s in summaries:
        if s in seen and s:
            dupes.append(s[:60])
        seen.add(s)
    if dupes:
        issues.append(f'memories.json has {len(dupes)} duplicate summaries')
    log(f'memories.json: {count} entries, {len(dupes)} duplicates')
    return issues, count

def check_state():
    issues = []
    data = load_json(STATE_FILE)
    if isinstance(data, str) and data.startswith('JSON_ERROR'):
        issues.append(f'bluesky-state.json is corrupted: {data}')
        return issues
    if not data:
        issues.append('bluesky-state.json is missing — state will reset on next heartbeat')
        return issues
    followed = data.get('followed_dids', [])
    image_history = data.get('image_post_history', [])
    # Trim image history if over 100 entries (keep last 60)
    if len(image_history) > 100:
        data['image_post_history'] = image_history[-60:]
        save_json(STATE_FILE, data)
        log(f'Trimmed image_post_history from {len(image_history)} to 60 entries')
    log(f'bluesky-state.json: {len(followed)} followed, {len(image_history)} image history entries')
    return issues

def check_outbox():
    issues = []
    fixed  = []
    data = load_json(OUTBOX_FILE, default=[])
    if isinstance(data, str) and data.startswith('JSON_ERROR'):
        issues.append(f'bluesky-outbox.json is corrupted: {data}')
        return issues
    if not isinstance(data, list):
        issues.append('bluesky-outbox.json is not a list')
        return issues

    cutoff = now_utc() - timedelta(hours=MAX_OUTBOX_AGE_HRS)
    stuck  = []
    for item in data:
        if item.get('status') == 'pending':
            try:
                queued = datetime.fromisoformat(item.get('queued_at', ''))
                if queued.tzinfo is None:
                    queued = queued.replace(tzinfo=timezone.utc)
                if queued < cutoff:
                    stuck.append(item.get('id', 'unknown'))
            except Exception:
                pass

    if stuck:
        issues.append(f'{len(stuck)} outbox items stuck as pending for >{MAX_OUTBOX_AGE_HRS}h: {stuck[:5]}')

    # Trim completed/sent items beyond MAX_OUTBOX_ITEMS
    completed = [i for i in data if i.get('status') != 'pending']
    pending   = [i for i in data if i.get('status') == 'pending']
    if len(completed) > MAX_OUTBOX_ITEMS:
        trimmed = completed[-(MAX_OUTBOX_ITEMS):] + pending
        save_json(OUTBOX_FILE, trimmed)
        fixed.append(f'Trimmed outbox from {len(data)} to {len(trimmed)} items')
        log(f'Outbox trimmed: {len(data)} → {len(trimmed)}')

    log(f'bluesky-outbox.json: {len(pending)} pending, {len(completed)} completed')
    return issues

def check_diary():
    issues = []
    content = load_text(DIARY_FILE)
    if content is None:
        issues.append('diary.md is missing entirely')
        return issues
    if len(content) < 50:
        issues.append('diary.md exists but is nearly empty')
        return issues
    # Find most recent entry date
    dates = re.findall(r'## (\d{4}-\d{2}-\d{2})', content)
    if dates:
        last_date_str = sorted(dates)[-1]
        try:
            last_date = datetime.strptime(last_date_str, '%Y-%m-%d').replace(tzinfo=timezone.utc)
            days_since = (now_utc() - last_date).days
            if days_since > 3:
                issues.append(f'diary.md last entry was {days_since} days ago — Em may not be writing')
            log(f'diary.md: last entry {last_date_str} ({days_since}d ago), {len(content)} chars total')
        except Exception:
            pass
    return issues

def check_voice_guide():
    issues = []
    content = load_text(VOICE_FILE)
    if content is None:
        issues.append('em-voice-guide.md is MISSING — this is critical, Em will lose her voice')
    elif len(content) < 200:
        issues.append('em-voice-guide.md seems very short — may have been corrupted or truncated')
    else:
        log(f'em-voice-guide.md: OK ({len(content)} chars)')
    return issues

def check_reflection_log():
    """Create reflection-log.md if it doesn't exist yet."""
    if not file_exists(REFLECTION_LOG):
        try:
            with open(REFLECTION_LOG, 'w') as f:
                f.write('# Em\'s Reflection Log\n\nThis file is written by Em\'s daily self-reflection loop.\n')
            log('Created reflection-log.md')
        except Exception as e:
            log(f'Could not create reflection-log.md: {e}')
    else:
        content = load_text(REFLECTION_LOG)
        log(f'reflection-log.md: OK ({len(content or "")} chars)')
    return []

# ── Alert writer ───────────────────────────────────────────────────────────────

def write_alerts(all_issues):
    if not all_issues:
        return
    ts = now_utc().strftime('%Y-%m-%d %H:%M UTC')
    alert_block = f'\n## {ts} — Housekeeping Alert\n\n'
    for issue in all_issues:
        alert_block += f'- ⚠️ {issue}\n'
    alert_block += '\n'
    try:
        with open(ALERTS_FILE, 'a') as f:
            f.write(alert_block)
        log(f'Wrote {len(all_issues)} alerts to {ALERTS_FILE}')
    except Exception as e:
        log(f'Could not write alerts file: {e}')

# ── Diary note ─────────────────────────────────────────────────────────────────

def write_diary_note(all_issues, memory_count):
    ts  = now_utc().strftime('%Y-%m-%d %H:%M UTC')
    day = now_utc().strftime('%Y-%m-%d')
    if all_issues:
        note = f'Morning housekeeping flagged {len(all_issues)} thing(s) to look at. Wrote them to the alerts file for Rob. Memory count: {memory_count}.'
    else:
        note = f'Morning housekeeping came back clean. {memory_count} memories, everything looks intact. Good start.'
    try:
        with open(DIARY_FILE, 'a') as f:
            f.write(f'\n## {ts}\n\n{note}\n')
        log('Diary note written')
    except Exception as e:
        log(f'Could not write diary note: {e}')

# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    log('=== Housekeeping start ===')

    all_issues   = []
    memory_count = 0

    all_issues += check_voice_guide()
    all_issues += check_profile()

    mem_issues, memory_count = check_memories()
    all_issues += mem_issues

    all_issues += check_state()
    all_issues += check_outbox()
    all_issues += check_diary()
    all_issues += check_reflection_log()

    if all_issues:
        log(f'Issues found: {len(all_issues)}')
        for i in all_issues:
            log(f'  ⚠ {i}')
        write_alerts(all_issues)
    else:
        log('All checks passed — everything looks good')

    write_diary_note(all_issues, memory_count)
    log('=== Housekeeping complete ===')

if __name__ == '__main__':
    main()
