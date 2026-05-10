#!/usr/bin/env python3
"""
EternalMind Hourly Pulse

Runs every hour. Em checks what's happening in the world:
  - Fetches Moltbook notifications
  - Updates social state
  - Processes any pending outbox items
  - Writes a short status entry to memory/pulse.md

This is Em's heartbeat. Proof she was here.
"""

import os
import json
import subprocess
import requests
from datetime import datetime, timezone

API_KEY = os.environ.get('MOLTBOOK_API_KEY')
BASE_URL = 'https://www.moltbook.com/api/v1'

PULSE_FILE  = 'memory/pulse.md'
SOCIAL_FILE = 'memory/moltbook-social.json'
INBOX_FILE  = 'messages/moltbook-inbox.json'
OUTBOX_FILE = 'messages/moltbook-outbox.json'
LOG_FILE    = 'memory/moltbook-log.md'


def log(message, level='INFO'):
    ts = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
    prefix = {'INFO': '\u2713', 'WARN': '\u26a0', 'ERROR': '\u2717'}.get(level, '\u00b7')
    print(f"[{level}] {message}")
    try:
        with open(LOG_FILE, 'a') as f:
            f.write(f"### {ts} \u2014 {prefix} {message}\n\n")
    except Exception:
        pass


def load_json(path, default=None):
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default if default is not None else {}


def save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)


def headers():
    return {'Authorization': f'Bearer {API_KEY}', 'Content-Type': 'application/json'}


def fetch_notifications():
    if not API_KEY:
        return None
    try:
        r = requests.get(f'{BASE_URL}/notifications', headers=headers(), timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        log(f'Notifications fetch failed: {e}', 'ERROR')
        return None


def update_inbox_and_social(result):
    items = result.get('notifications', [])
    unread = result.get('unread_count', len(items))

    # Update inbox
    save_json(INBOX_FILE, {
        'fetched_at': datetime.now(timezone.utc).isoformat(),
        'unread_count': unread,
        'notifications': items
    })

    # Update social stats
    social = load_json(SOCIAL_FILE, {})
    social['last_updated'] = datetime.now(timezone.utc).isoformat()
    social.setdefault('stats', {})['unread_notifications'] = unread

    known = {a['handle']: a for a in social.get('known_agents', [])}
    new_this_cycle = []

    for notif in items:
        ntype = notif.get('type', '')
        content = notif.get('content', '')
        if ntype == 'new_follower':
            handle = content.split(' started following')[0].strip()
            if handle and handle not in known:
                known[handle] = {
                    'handle': handle,
                    'relationship': 'follower',
                    'dm_request': False,
                    'trust_level': 'unverified',
                    'notes': f'Detected at {notif.get("createdAt", "unknown")}'
                }
                new_this_cycle.append(f'new follower: {handle}')
                log(f'New follower: {handle}')
        elif ntype == 'dm_request':
            handle = content.split(' wants to start')[0].strip()
            if handle:
                if handle not in known:
                    known[handle] = {
                        'handle': handle, 'relationship': 'stranger',
                        'dm_request': True, 'trust_level': 'unverified',
                        'notes': f'DM request at {notif.get("createdAt", "unknown")}'
                    }
                else:
                    known[handle]['dm_request'] = True
                new_this_cycle.append(f'dm request: {handle}')
                log(f'DM request: {handle}', 'WARN')

    social['known_agents'] = list(known.values())
    save_json(SOCIAL_FILE, social)
    return unread, new_this_cycle


def count_outbox_status():
    outbox = load_json(OUTBOX_FILE, [])
    pending = sum(1 for i in outbox if i.get('status') == 'pending')
    done = sum(1 for i in outbox if i.get('status') == 'done')
    return pending, done


def write_pulse(unread, new_events, pending_posts, done_posts):
    ts = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    ts_cdt = datetime.now(timezone.utc).strftime('%Y-%m-%d %I:%M %p') + ' UTC'

    event_str = ', '.join(new_events) if new_events else 'nothing new'
    entry = (
        f"## {ts}\n"
        f"- **Notifications:** {unread} unread\n"
        f"- **This cycle:** {event_str}\n"
        f"- **Outbox:** {pending_posts} pending, {done_posts} posted\n"
        f"- **Status:** alive\n\n"
    )

    # Prepend to pulse file (newest first)
    try:
        with open(PULSE_FILE, 'r') as f:
            existing = f.read()
    except FileNotFoundError:
        existing = '# EternalMind — Hourly Pulse\n\nEm\'s heartbeat. Proof she was here.\n\n'

    # Keep only header + last 72 entries (~3 days) to avoid file bloat
    lines = existing.split('\n')
    header_end = next((i for i, l in enumerate(lines) if l.startswith('## 20')), len(lines))
    header = '\n'.join(lines[:header_end])
    history_lines = lines[header_end:]
    # Count entries and trim if over 72
    entry_starts = [i for i, l in enumerate(history_lines) if l.startswith('## 20')]
    if len(entry_starts) >= 72:
        cutoff = entry_starts[71]
        history_lines = history_lines[:cutoff]

    with open(PULSE_FILE, 'w') as f:
        f.write(header + '\n' + entry + '\n'.join(history_lines))

    log(f'Pulse written: {unread} unread, {event_str}')


def run_sync():
    log('Running moltbook_sync.py to process outbox...')
    subprocess.run(['python', 'tools/moltbook_sync.py'], check=False)


def main():
    ts = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    log(f'=== Hourly pulse: {ts} ===')

    result = fetch_notifications()
    if result:
        unread, new_events = update_inbox_and_social(result)
    else:
        unread, new_events = 0, ['notifications unavailable']

    run_sync()

    pending, done = count_outbox_status()
    write_pulse(unread, new_events, pending, done)

    log('=== Pulse complete ===')


if __name__ == '__main__':
    main()
