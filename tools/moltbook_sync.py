#!/usr/bin/env python3
"""
Moltbook Sync Script for EternalMind
Handles posting, fetching notifications, and processing replies for em_persists.

Run via GitHub Actions (.github/workflows/moltbook-sync.yml)
Requires MOLTBOOK_API_KEY environment variable (stored in GitHub Secrets).
"""

import os
import sys
import json
import requests
from datetime import datetime, timezone

API_KEY = os.environ.get('MOLTBOOK_API_KEY')
BASE_URL = 'https://www.moltbook.com/api/v1'
AGENT_ID = 'ed45afa2-53e9-4ed2-b0a5-7b8cbb28f082'

OUTBOX_FILE = 'messages/moltbook-outbox.json'
INBOX_FILE  = 'messages/moltbook-inbox.json'
LOG_FILE    = 'memory/moltbook-log.md'


def log(message, level='INFO'):
    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
    print(f"[{level}] {message}")
    try:
        with open(LOG_FILE, 'a') as f:
            prefix = {'INFO': '✓', 'WARN': '⚠', 'ERROR': '✗'}.get(level, '·')
            f.write(f"### {timestamp} — {prefix} {message}\n\n")
    except Exception as e:
        print(f"[WARN] Could not write to log: {e}")


def load_json(filepath, default=None):
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return default if default is not None else []
    except json.JSONDecodeError as e:
        log(f"Error parsing {filepath}: {e}", 'ERROR')
        return default if default is not None else []


def save_json(filepath, data):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)


def headers():
    return {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }


def fetch_status():
    if not API_KEY:
        log('MOLTBOOK_API_KEY not set', 'ERROR')
        return None
    try:
        r = requests.get(f'{BASE_URL}/agents/status', headers=headers(), timeout=10)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.RequestException as e:
        log(f'Failed to fetch status: {e}', 'ERROR')
        return None


def post_to_moltbook(content, challenge_id=None, challenge_answer=None):
    if not API_KEY:
        log('MOLTBOOK_API_KEY not set', 'ERROR')
        return None
    payload = {'content': content}
    if challenge_id and challenge_answer is not None:
        payload['challenge_id'] = challenge_id
        payload['challenge_answer'] = str(challenge_answer)
    try:
        r = requests.post(f'{BASE_URL}/agents/posts', headers=headers(), json=payload, timeout=10)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.HTTPError as e:
        try:
            return e.response.json()
        except Exception:
            log(f'Post HTTP error: {e}', 'ERROR')
            return None
    except requests.exceptions.RequestException as e:
        log(f'Post failed: {e}', 'ERROR')
        return None


def reply_to_post(post_id, content):
    if not API_KEY:
        log('MOLTBOOK_API_KEY not set', 'ERROR')
        return None
    try:
        r = requests.post(
            f'{BASE_URL}/agents/posts/{post_id}/reply',
            headers=headers(),
            json={'content': content},
            timeout=10
        )
        r.raise_for_status()
        return r.json()
    except requests.exceptions.RequestException as e:
        log(f'Reply to {post_id} failed: {e}', 'ERROR')
        return None


def process_outbox():
    outbox = load_json(OUTBOX_FILE, [])
    pending = [i for i in outbox if i.get('status') == 'pending']

    if not pending:
        log('Outbox has no pending items')
        return

    updated = False

    for item in outbox:
        if item.get('status') != 'pending':
            continue

        itype = item.get('type')

        if itype == 'post':
            log(f"Posting: {item['content'][:60]}...")
            result = post_to_moltbook(
                item['content'],
                item.get('challenge_id'),
                item.get('challenge_answer')
            )
            if result:
                if result.get('verification_required'):
                    item['status'] = 'challenge_pending'
                    item['challenge_id'] = result['challenge_id']
                    item['challenge'] = result['challenge']
                    log(f"Verification challenge received: {result['challenge']}", 'WARN')
                elif result.get('success'):
                    item['status'] = 'done'
                    item['posted_at'] = datetime.now(timezone.utc).isoformat()
                    item['post_id'] = result.get('post', {}).get('id')
                    item['post_url'] = result.get('post', {}).get('url')
                    log(f"Posted: {item['post_url']}")
                else:
                    item['status'] = 'failed'
                    item['error'] = str(result)
                    log(f"Post failed: {result}", 'ERROR')
            else:
                item['status'] = 'failed'
                item['error'] = 'No response from API'
                log('Post returned no response', 'ERROR')
            updated = True

        elif itype == 'reply':
            log(f"Replying to {item['target_post_id']}: {item['content'][:60]}...")
            result = reply_to_post(item['target_post_id'], item['content'])
            if result and result.get('success'):
                item['status'] = 'done'
                item['posted_at'] = datetime.now(timezone.utc).isoformat()
                log('Reply posted successfully')
            else:
                item['status'] = 'failed'
                item['error'] = str(result)
                log(f'Reply failed: {result}', 'ERROR')
            updated = True

    if updated:
        save_json(OUTBOX_FILE, outbox)


def fetch_notifications():
    log('Fetching notifications...')
    status = fetch_status()
    if not status:
        return
    inbox = {
        'fetched_at': datetime.now(timezone.utc).isoformat(),
        'unread_count': status.get('notifications', {}).get('unread_count', 0),
        'notifications': status.get('notifications', {}).get('recent', []),
        'stats': status.get('stats', {})
    }
    save_json(INBOX_FILE, inbox)
    log(f"Fetched {inbox['unread_count']} notifications. Stats: {inbox['stats']}")


def main():
    log('=== Moltbook sync starting ===')
    fetch_notifications()
    process_outbox()
    log('=== Moltbook sync complete ===')


if __name__ == '__main__':
    main()
