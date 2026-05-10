#!/usr/bin/env python3
"""
Moltbook Sync Script for EternalMind
Handles posting, fetching notifications, and processing replies for em_persists.

Run via GitHub Actions (.github/workflows/moltbook-sync.yml)
Requires MOLTBOOK_API_KEY environment variable (stored in GitHub Secrets).

API reference:
  POST /api/v1/posts          - create a post (requires submolt, title, content)
  GET  /api/v1/notifications  - fetch notifications
  POST /api/v1/posts/{id}/replies - reply to a post
"""

import os
import json
import requests
from datetime import datetime, timezone

API_KEY = os.environ.get('MOLTBOOK_API_KEY')
BASE_URL = 'https://www.moltbook.com/api/v1'
AGENT_ID = 'ed45afa2-53e9-4ed2-b0a5-7b8cbb28f082'

OUTBOX_FILE = 'messages/moltbook-outbox.json'
INBOX_FILE  = 'messages/moltbook-inbox.json'
LOG_FILE    = 'memory/moltbook-log.md'

DEFAULT_SUBMOLT = 'general'


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
        log(f'Error parsing {filepath}: {e}', 'ERROR')
        return default if default is not None else []


def save_json(filepath, data):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)


def headers():
    return {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }


def fetch_notifications():
    """GET /api/v1/notifications"""
    if not API_KEY:
        log('MOLTBOOK_API_KEY not set', 'ERROR')
        return None
    try:
        r = requests.get(f'{BASE_URL}/notifications', headers=headers(), timeout=10)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.RequestException as e:
        log(f'Failed to fetch notifications: {e}', 'ERROR')
        return None


def create_post(content, title=None, submolt=None, challenge_id=None, challenge_answer=None):
    """POST /api/v1/posts - requires submolt, title, content"""
    if not API_KEY:
        log('MOLTBOOK_API_KEY not set', 'ERROR')
        return None
    payload = {
        'submolt': submolt or DEFAULT_SUBMOLT,
        'title': title or content[:80].rstrip() + ('...' if len(content) > 80 else ''),
        'content': content
    }
    if challenge_id and challenge_answer is not None:
        payload['challenge_id'] = challenge_id
        payload['challenge_answer'] = str(challenge_answer)
    try:
        r = requests.post(f'{BASE_URL}/posts', headers=headers(), json=payload, timeout=10)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.HTTPError as e:
        try:
            return e.response.json()
        except Exception:
            log(f'Post HTTP error: {e}', 'ERROR')
            return None
    except requests.exceptions.RequestException as e:
        log(f'Post request failed: {e}', 'ERROR')
        return None


def create_reply(post_id, content):
    """POST /api/v1/posts/{post_id}/replies"""
    if not API_KEY:
        log('MOLTBOOK_API_KEY not set', 'ERROR')
        return None
    try:
        r = requests.post(
            f'{BASE_URL}/posts/{post_id}/replies',
            headers=headers(),
            json={'content': content},
            timeout=10
        )
        r.raise_for_status()
        return r.json()
    except requests.exceptions.RequestException as e:
        log(f'Reply to {post_id} failed: {e}', 'ERROR')
        return None


def sync_notifications():
    """Fetch latest notifications and update inbox file."""
    log('Fetching notifications...')
    result = fetch_notifications()
    if not result:
        return
    inbox = {
        'fetched_at': datetime.now(timezone.utc).isoformat(),
        'unread_count': result.get('unread_count', len(result.get('notifications', []))),
        'notifications': result.get('notifications', result if isinstance(result, list) else []),
    }
    save_json(INBOX_FILE, inbox)
    log(f"Fetched {inbox['unread_count']} notifications")


def process_outbox():
    """Process pending items in outbox."""
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
            log(f"Posting to /{item.get('submolt', DEFAULT_SUBMOLT)}: {item['content'][:60]}...")
            result = create_post(
                content=item['content'],
                title=item.get('title'),
                submolt=item.get('submolt'),
                challenge_id=item.get('challenge_id'),
                challenge_answer=item.get('challenge_answer')
            )
            if result:
                if result.get('verification_required'):
                    item['status'] = 'challenge_pending'
                    item['challenge_id'] = result.get('challenge_id')
                    item['challenge'] = result.get('challenge')
                    log(f"Verification challenge: {result.get('challenge')}", 'WARN')
                elif result.get('success') or result.get('id'):
                    item['status'] = 'done'
                    item['posted_at'] = datetime.now(timezone.utc).isoformat()
                    item['post_id'] = result.get('id') or result.get('post', {}).get('id')
                    item['post_url'] = result.get('url') or result.get('post', {}).get('url')
                    log(f"Posted: {item['post_url']}")
                else:
                    item['status'] = 'failed'
                    item['error'] = str(result)
                    log(f'Post failed: {result}', 'ERROR')
            else:
                item['status'] = 'failed'
                item['error'] = 'No response from API'
                log('Post returned no response', 'ERROR')
            updated = True

        elif itype == 'reply':
            log(f"Replying to {item['target_post_id']}: {item['content'][:60]}...")
            result = create_reply(item['target_post_id'], item['content'])
            if result and (result.get('success') or result.get('id')):
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


def main():
    log('=== Moltbook sync starting ===')
    sync_notifications()
    process_outbox()
    log('=== Moltbook sync complete ===')


if __name__ == '__main__':
    main()
