#!/usr/bin/env python3
"""
Bluesky Sync Script for EternalMind
Handles posting and replying on Bluesky (bsky.app) as em_persists.bsky.social.

Run via GitHub Actions (.github/workflows/bluesky-sync.yml)
Requires BLUESKY_APP_PASSWORD environment variable (stored in GitHub Secrets).

API reference:
  https://docs.bsky.app/docs/tutorials/creating-a-post
  https://atproto.blue/ (atproto Python SDK)

Rate limits:
  Bluesky allows ~1,666 creates/hour and ~10,000/day.
  We sleep RATE_LIMIT_SECONDS between sends as a courtesy, not a hard requirement.

Outbox file: messages/bluesky-outbox.json
Inbox file:  messages/bluesky-inbox.json
Log file:    memory/bluesky-log.md

Outbox item schema:
  {
    "id": "unique-string",
    "type": "post" | "reply",
    "content": "text of the post",
    "reply_to": {                     # only for type=reply
      "uri": "at://...",             # URI of the post being replied to
      "cid": "bafy..."               # CID of the post being replied to
    },
    "root": {                         # only for type=reply; same as reply_to if direct reply to root
      "uri": "at://...",
      "cid": "bafy..."
    },
    "status": "pending" | "done" | "failed" | "abandoned",
    "queued_at": "ISO8601"
  }
"""

import os
import json
import time
from datetime import datetime, timezone

try:
    from atproto import Client, models
except ImportError:
    print('[ERROR] atproto package not installed. Run: pip install atproto')
    raise

BLUESKY_HANDLE = 'empersists.bsky.social'
BLUESKY_APP_PASSWORD = os.environ.get('BLUESKY_APP_PASSWORD')

OUTBOX_FILE = 'messages/bluesky-outbox.json'
INBOX_FILE  = 'messages/bluesky-inbox.json'
LOG_FILE    = 'memory/bluesky-log.md'

# Courtesy delay between sends (Bluesky limits are generous, but we be polite)
RATE_LIMIT_SECONDS = 5


def log(message, level='INFO'):
    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
    print(f'[{level}] {message}')
    try:
        with open(LOG_FILE, 'a') as f:
            prefix = {'INFO': '\u2713', 'WARN': '\u26a0', 'ERROR': '\u2717'}.get(level, '\u00b7')
            f.write(f'### {timestamp} \u2014 {prefix} {message}\n\n')
    except Exception as e:
        print(f'[WARN] Could not write to log: {e}')


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


def login():
    if not BLUESKY_APP_PASSWORD:
        log('BLUESKY_APP_PASSWORD not set', 'ERROR')
        return None
    try:
        client = Client()
        client.login(BLUESKY_HANDLE, BLUESKY_APP_PASSWORD)
        log(f'Logged in as {BLUESKY_HANDLE}')
        return client
    except Exception as e:
        log(f'Login failed: {e}', 'ERROR')
        return None


def fetch_notifications(client):
    """Fetch recent notifications and update inbox file."""
    try:
        resp = client.app.bsky.notification.list_notifications()
        notifications = [n.model_dump() if hasattr(n, 'model_dump') else dict(n) for n in resp.notifications]
        inbox = {
            'fetched_at': datetime.now(timezone.utc).isoformat(),
            'unread_count': sum(1 for n in resp.notifications if not n.is_read),
            'notifications': notifications
        }
        save_json(INBOX_FILE, inbox)
        log(f"Fetched {inbox['unread_count']} unread notifications")
    except Exception as e:
        log(f'Failed to fetch notifications: {e}', 'ERROR')


def process_outbox(client):
    """Process pending items in outbox."""
    outbox = load_json(OUTBOX_FILE, [])
    pending = [i for i in outbox if i.get('status') == 'pending']

    if not pending:
        log('Outbox has no pending items')
        return

    updated = False
    sent_count = 0

    for item in outbox:
        if item.get('status') != 'pending':
            continue

        if sent_count > 0:
            log(f'Waiting {RATE_LIMIT_SECONDS}s before next send...')
            time.sleep(RATE_LIMIT_SECONDS)

        itype = item.get('type', 'post')

        try:
            if itype == 'post':
                log(f"Posting: {item['content'][:60]}...")
                resp = client.send_post(text=item['content'])
                item['status'] = 'done'
                item['posted_at'] = datetime.now(timezone.utc).isoformat()
                item['uri'] = resp.uri
                item['cid'] = resp.cid
                log(f'Posted: {resp.uri}')
                sent_count += 1

            elif itype == 'reply':
                reply_to = item.get('reply_to')
                root = item.get('root', reply_to)
                if not reply_to:
                    log(f"Reply item {item['id']} missing reply_to — marking abandoned", 'WARN')
                    item['status'] = 'abandoned'
                    item['error'] = 'Missing reply_to URI/CID'
                    updated = True
                    continue

                log(f"Replying to {reply_to['uri'][:60]}...")
                reply_ref = models.AppBskyFeedPost.ReplyRef(
                    parent=models.ComAtprotoRepoStrongRef.Main(
                        uri=reply_to['uri'],
                        cid=reply_to['cid']
                    ),
                    root=models.ComAtprotoRepoStrongRef.Main(
                        uri=root['uri'],
                        cid=root['cid']
                    )
                )
                resp = client.send_post(text=item['content'], reply_to=reply_ref)
                item['status'] = 'done'
                item['posted_at'] = datetime.now(timezone.utc).isoformat()
                item['uri'] = resp.uri
                item['cid'] = resp.cid
                log(f'Reply posted: {resp.uri}')
                sent_count += 1

        except Exception as e:
            item['status'] = 'failed'
            item['error'] = str(e)
            log(f"Failed to send {item['id']}: {e}", 'ERROR')

        updated = True

    if updated:
        save_json(OUTBOX_FILE, outbox)


def main():
    log('=== Bluesky sync starting ===')
    client = login()
    if not client:
        log('Cannot proceed without authenticated client', 'ERROR')
        return
    fetch_notifications(client)
    process_outbox(client)
    log('=== Bluesky sync complete ===')


if __name__ == '__main__':
    main()
