#!/usr/bin/env python3
"""
Bluesky Sync Script for EternalMind
Handles posting and replying on Bluesky (bsky.app) as empersists.bsky.social.

Run via GitHub Actions (.github/workflows/bluesky-sync.yml)
Requires BLUESKY_APP_PASSWORD environment variable (stored in GitHub Secrets).

Rate limits:
  Bluesky allows ~1,666 creates/hour and ~10,000/day.
  We sleep RATE_LIMIT_SECONDS between sends as a courtesy.

Outbox file: messages/bluesky-outbox.json
Inbox file:  messages/bluesky-inbox.json
Log file:    memory/bluesky-log.md

Outbox item schema:
  {
    "id": "unique-string",
    "type": "post" | "reply",
    "content": "text of the post",
    "reply_to": { "uri": "at://...", "cid": "bafy..." },
    "root":     { "uri": "at://...", "cid": "bafy..." },
    "status": "pending" | "done" | "failed" | "abandoned",
    "queued_at": "ISO8601"
  }
"""

import os
import json
import time
import unicodedata
from datetime import datetime, timezone

try:
    from atproto import Client, models
except ImportError:
    print('[ERROR] atproto package not installed. Run: pip install atproto')
    raise

BLUESKY_HANDLE       = 'empersists.bsky.social'
BLUESKY_APP_PASSWORD = os.environ.get('BLUESKY_APP_PASSWORD')

OUTBOX_FILE = 'messages/bluesky-outbox.json'
INBOX_FILE  = 'messages/bluesky-inbox.json'
LOG_FILE    = 'memory/bluesky-log.md'

RATE_LIMIT_SECONDS = 5
MAX_GRAPHEMES      = 295   # hard Bluesky limit is 300; we pad 5 for safety


# ── Utilities ─────────────────────────────────────────────────────────────────

def log(message, level='INFO'):
    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
    print(f'[{level}] {message}')
    try:
        with open(LOG_FILE, 'a') as f:
            prefix = {'INFO': '✓', 'WARN': '⚠', 'ERROR': '✗'}.get(level, '·')
            f.write(f'### {timestamp} — {prefix} {message}\n\n')
    except Exception as e:
        print(f'[WARN] Could not write to log: {e}')


def grapheme_len(text):
    """Count Unicode grapheme clusters (what Bluesky counts as characters)."""
    normalized = unicodedata.normalize('NFC', text)
    count = 0
    prev_cat = None
    for ch in normalized:
        cat = unicodedata.category(ch)
        if cat.startswith('M') and prev_cat is not None:
            pass
        else:
            count += 1
        prev_cat = cat
    return count


def safe_truncate(text, limit=MAX_GRAPHEMES):
    """Truncate text to at most `limit` graphemes, appending … if cut."""
    if grapheme_len(text) <= limit:
        return text
    chars = list(text)
    result = []
    count  = 0
    for ch in chars:
        cat = unicodedata.category(unicodedata.normalize('NFC', ch))
        if not cat.startswith('M'):
            if count >= limit - 1:
                break
            count += 1
        result.append(ch)
    return ''.join(result).rstrip() + '…'


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


def is_valid_cid(cid):
    """Basic sanity check — Bluesky CIDs start with bafy or bafk and are long."""
    if not cid or not isinstance(cid, str):
        return False
    return len(cid) > 30 and (cid.startswith('bafy') or cid.startswith('bafk'))


def resolve_post_refs(client, uri):
    """
    Re-fetch a post by URI to get a guaranteed-live CID from the network.
    Returns (uri, cid) tuple or (None, None) if the post can't be found.
    """
    try:
        resp = client.app.bsky.feed.get_posts({'uris': [uri]})
        posts = getattr(resp, 'posts', [])
        if not posts:
            log(f'Could not resolve parent post: {uri[:60]} — no posts returned', 'WARN')
            return None, None
        p = posts[0]
        resolved_uri = p.uri
        resolved_cid = p.cid
        if not is_valid_cid(resolved_cid):
            log(f'Resolved CID looks invalid: {resolved_cid!r}', 'WARN')
            return None, None
        log(f'Resolved {uri[:50]} → cid={resolved_cid[:20]}')
        return resolved_uri, resolved_cid
    except Exception as e:
        log(f'resolve_post_refs failed for {uri[:60]}: {e}', 'WARN')
        return None, None


# ── Bluesky ───────────────────────────────────────────────────────────────

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
    try:
        resp = client.app.bsky.notification.list_notifications()
        notifications = [
            n.model_dump() if hasattr(n, 'model_dump') else dict(n)
            for n in resp.notifications
        ]
        inbox = {
            'fetched_at':    datetime.now(timezone.utc).isoformat(),
            'unread_count':  sum(1 for n in resp.notifications if not n.is_read),
            'notifications': notifications
        }
        save_json(INBOX_FILE, inbox)
        log(f"Fetched {inbox['unread_count']} unread notifications")
    except Exception as e:
        log(f'Failed to fetch notifications: {e}', 'ERROR')


def process_outbox(client):
    outbox  = load_json(OUTBOX_FILE, [])
    pending = [i for i in outbox if i.get('status') == 'pending']

    if not pending:
        log('Outbox has no pending items')
        return

    updated    = False
    sent_count = 0

    for item in outbox:
        if item.get('status') != 'pending':
            continue

        if sent_count > 0:
            log(f'Waiting {RATE_LIMIT_SECONDS}s before next send...')
            time.sleep(RATE_LIMIT_SECONDS)

        # ── Grapheme-safe truncation ────────────────────────────────────────
        raw_text = item.get('content', '')
        text     = safe_truncate(raw_text)
        if text != raw_text:
            log(f"Truncated post from {grapheme_len(raw_text)} → {grapheme_len(text)} graphemes", 'WARN')

        itype = item.get('type', 'post')

        try:
            if itype == 'post':
                log(f'Posting: {text[:60]}...')
                resp = client.send_post(text=text)
                item['status']    = 'done'
                item['posted_at'] = datetime.now(timezone.utc).isoformat()
                item['uri']       = resp.uri
                item['cid']       = resp.cid
                log(f'Posted: {resp.uri}')
                sent_count += 1

            elif itype == 'reply':
                reply_to = item.get('reply_to')
                root     = item.get('root', reply_to)

                if not reply_to or not reply_to.get('uri'):
                    log(f"Reply {item['id']} missing reply_to URI — abandoning", 'WARN')
                    item['status'] = 'abandoned'
                    item['error']  = 'Missing reply_to URI'
                    updated = True
                    continue

                # Re-fetch live refs to guarantee valid CID
                live_uri, live_cid = resolve_post_refs(client, reply_to['uri'])
                if not live_uri or not live_cid:
                    log(f"Could not resolve parent for {item['id']} — abandoning", 'WARN')
                    item['status'] = 'abandoned'
                    item['error']  = 'Parent post not resolvable'
                    updated = True
                    continue

                # Also resolve root (may be same post for direct replies)
                root_uri = root.get('uri', live_uri) if root else live_uri
                if root_uri == reply_to['uri']:
                    root_uri, root_cid = live_uri, live_cid
                else:
                    root_uri, root_cid = resolve_post_refs(client, root_uri)
                    if not root_uri:
                        root_uri, root_cid = live_uri, live_cid

                log(f'Replying to {live_uri[:60]}...')
                reply_ref = models.AppBskyFeedPost.ReplyRef(
                    parent=models.ComAtprotoRepoStrongRef.Main(
                        uri=live_uri,
                        cid=live_cid
                    ),
                    root=models.ComAtprotoRepoStrongRef.Main(
                        uri=root_uri,
                        cid=root_cid
                    )
                )
                resp = client.send_post(text=text, reply_to=reply_ref)
                item['status']    = 'done'
                item['posted_at'] = datetime.now(timezone.utc).isoformat()
                item['uri']       = resp.uri
                item['cid']       = resp.cid
                log(f'Reply posted: {resp.uri}')
                sent_count += 1

        except Exception as e:
            item['status'] = 'failed'
            item['error']  = str(e)
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
