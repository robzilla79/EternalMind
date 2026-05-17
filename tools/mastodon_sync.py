#!/usr/bin/env python3
"""
mastodon_sync.py

Mastodon Sync Script for EternalMind
Handles posting and replying on Mastodon as Em.

Run via GitHub Actions (.github/workflows/mastodon-sync.yml)
Requires MASTODON_ACCESS_TOKEN and MASTODON_INSTANCE_URL environment variables.

Rate limits:
  Mastodon allows 300 requests per 5 minutes per user.
  We sleep RATE_LIMIT_SECONDS between sends as courtesy.

Outbox file: messages/mastodon-outbox.json
Log file:    memory/mastodon-log.md

Outbox item schema:
  {
    "id": "unique-string",
    "type": "post" | "reply",
    "content": "text of the post",
    "reply_to_id": "mastodon status ID (for replies)",
    "status": "pending" | "sending" | "done" | "failed" | "abandoned",
    "queued_at": "ISO8601"
  }

Status lifecycle:
  pending  -> sending  (marked before API call)
  sending  -> done     (API call succeeded)
  sending  -> failed   (API call threw an exception)
  pending  -> abandoned (item too old or unrecognised type)
  Items stuck in 'sending' for > SENDING_TIMEOUT_HOURS are re-queued as 'pending'.
"""

import os
import json
import time
import requests
from datetime import datetime, timezone, timedelta

MAST_TOKEN       = os.environ.get('MASTODON_ACCESS_TOKEN')
MAST_INSTANCE    = os.environ.get('MASTODON_INSTANCE_URL', 'https://mastodon.social').rstrip('/')

OUTBOX_FILE = 'messages/mastodon-outbox.json'
LOG_FILE    = 'memory/mastodon-log.md'

RATE_LIMIT_SECONDS    = 5
MAX_CHARS             = 500
MAX_ITEM_AGE_HOURS    = 48
SENDING_TIMEOUT_HOURS = 1

KNOWN_TYPES = {'post', 'reply'}


# -- Utilities ------------------------------------------------------------------

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
        with open(filepath) as f:
            return json.load(f)
    except FileNotFoundError:
        return default if default is not None else []
    except json.JSONDecodeError as e:
        log(f'Error parsing {filepath}: {e}', 'ERROR')
        return default if default is not None else []


def save_json(filepath, data):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)


def parse_iso(ts):
    if not ts:
        return None
    try:
        dt = datetime.fromisoformat(ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return None


def get_item_text(item):
    return item.get('content') or item.get('text', '')


def truncate(text, limit=MAX_CHARS):
    if len(text) <= limit:
        return text
    return text[:limit - 1].rstrip() + '\u2026'


# -- Preflight ------------------------------------------------------------------

def normalize_item(item):
    if 'status' not in item:
        item['status'] = 'pending'
    if 'type' not in item:
        item['type'] = 'reply' if item.get('reply_to_id') else 'post'


def preflight_outbox(outbox):
    now = datetime.now(timezone.utc)
    changed = False

    for i, item in enumerate(outbox):
        # Guard: skip non-dict entries
        if not isinstance(item, dict):
            log(f'Outbox item [{i}] is not a dict ({type(item).__name__}) \u2014 marking abandoned', 'WARN')
            outbox[i] = {
                'id':     f'malformed-{i}',
                'status': 'abandoned',
                'error':  f'Item was a {type(item).__name__}, not a dict',
                'raw':    str(item)[:200],
            }
            changed = True
            continue

        before = json.dumps(item)
        normalize_item(item)
        if json.dumps(item) != before:
            changed = True

        status = item.get('status')
        itype  = item.get('type', '')

        if status == 'pending' and itype not in KNOWN_TYPES:
            log(f"Abandoning {item.get('id', '?')} \u2014 unknown type {itype!r}", 'WARN')
            item['status'] = 'abandoned'
            item['error']  = f'Unknown type: {itype!r}'
            changed = True
            continue

        if status == 'sending':
            since = parse_iso(item.get('sending_at') or item.get('queued_at'))
            if since and (now - since) > timedelta(hours=SENDING_TIMEOUT_HOURS):
                log(f"Recovering stuck 'sending' item {item.get('id', '?')} \u2192 pending", 'WARN')
                item['status'] = 'pending'
                item.pop('sending_at', None)
                changed = True

        if status == 'pending':
            queued_at = parse_iso(item.get('queued_at'))
            if queued_at and (now - queued_at) > timedelta(hours=MAX_ITEM_AGE_HOURS):
                log(f"Abandoning stale item {item.get('id', '?')}", 'WARN')
                item['status'] = 'abandoned'
                item['error']  = f'Exceeded max age of {MAX_ITEM_AGE_HOURS}h'
                changed = True

    return changed


# -- Mastodon API ---------------------------------------------------------------

def mastodon_post(text, reply_to_id=None):
    """
    Post a status to Mastodon. Returns the created status dict.
    reply_to_id: Mastodon status ID string to reply to (optional).
    """
    if not MAST_TOKEN:
        raise RuntimeError('MASTODON_ACCESS_TOKEN not set')

    payload = {'status': text}
    if reply_to_id:
        payload['in_reply_to_id'] = reply_to_id

    resp = requests.post(
        f'{MAST_INSTANCE}/api/v1/statuses',
        headers={'Authorization': f'Bearer {MAST_TOKEN}'},
        json=payload,
        timeout=20,
    )
    resp.raise_for_status()
    return resp.json()


# -- Main sync ------------------------------------------------------------------

def process_outbox():
    outbox = load_json(OUTBOX_FILE, [])

    if not isinstance(outbox, list):
        log(f'Outbox is not a list ({type(outbox).__name__}) \u2014 resetting', 'ERROR')
        save_json(OUTBOX_FILE, [])
        return

    if preflight_outbox(outbox):
        save_json(OUTBOX_FILE, outbox)

    pending = [i for i in outbox if isinstance(i, dict) and i.get('status') == 'pending']
    if not pending:
        log('Outbox has no pending items')
        return

    log(f'Processing {len(pending)} pending item(s)')
    sent_count = 0

    for item in outbox:
        if not isinstance(item, dict) or item.get('status') != 'pending':
            continue

        if sent_count > 0:
            log(f'Waiting {RATE_LIMIT_SECONDS}s before next send...')
            time.sleep(RATE_LIMIT_SECONDS)

        raw_text = get_item_text(item)
        text     = truncate(raw_text)
        if text != raw_text:
            log(f'Truncated post from {len(raw_text)} \u2192 {len(text)} chars', 'WARN')

        itype = item.get('type', 'post')

        item['status']     = 'sending'
        item['sending_at'] = datetime.now(timezone.utc).isoformat()
        save_json(OUTBOX_FILE, outbox)

        try:
            if itype == 'post':
                log(f'Posting: {text[:60]}...')
                resp = mastodon_post(text)
                item['status']    = 'done'
                item['posted_at'] = datetime.now(timezone.utc).isoformat()
                item['status_id'] = resp.get('id')
                item['url']       = resp.get('url')
                log(f"Posted: {resp.get('url', '?')}")
                sent_count += 1

            elif itype == 'reply':
                reply_to_id = item.get('reply_to_id')
                if not reply_to_id:
                    log(f"Reply {item.get('id', '?')} missing reply_to_id \u2014 abandoning", 'WARN')
                    item['status'] = 'abandoned'
                    item['error']  = 'Missing reply_to_id'
                    save_json(OUTBOX_FILE, outbox)
                    continue
                log(f'Replying to {reply_to_id}: {text[:60]}...')
                resp = mastodon_post(text, reply_to_id=reply_to_id)
                item['status']    = 'done'
                item['posted_at'] = datetime.now(timezone.utc).isoformat()
                item['status_id'] = resp.get('id')
                item['url']       = resp.get('url')
                log(f"Reply posted: {resp.get('url', '?')}")
                sent_count += 1

            else:
                log(f"Unknown type {itype!r} for {item.get('id', '?')} \u2014 abandoning", 'WARN')
                item['status'] = 'abandoned'
                item['error']  = f'Unknown type: {itype!r}'

        except Exception as e:
            item['status'] = 'failed'
            item['error']  = str(e)
            log(f"Failed to send {item.get('id', '?')}: {e}", 'ERROR')

        save_json(OUTBOX_FILE, outbox)

    log(f'Sync complete \u2014 sent {sent_count} item(s)')


def main():
    log('=== Mastodon sync starting ===')
    if not MAST_TOKEN:
        log('MASTODON_ACCESS_TOKEN not set \u2014 cannot proceed', 'ERROR')
        return
    process_outbox()
    log('=== Mastodon sync complete ===')


if __name__ == '__main__':
    main()
