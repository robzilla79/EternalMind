#!/usr/bin/env python3
"""
bluesky_sync.py

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
    "type": "post" | "reply" | "image_post",
    "content": "text of the post",          # preferred key
    "text": "text of the post",             # accepted fallback
    "image_url": "https://... (optional, for image_post type)",
    "image_alt": "alt text for image (optional)",
    "reply_to": { "uri": "at://...", "cid": "bafy..." },
    "reply_to_uri": "at://..."              # accepted string fallback for reply_to
    "root":     { "uri": "at://...", "cid": "bafy..." },
    "status": "pending" | "sending" | "done" | "failed" | "abandoned",
                                             # omitted status treated as "pending"
    "queued_at": "ISO8601"
  }

Status lifecycle:
  pending  → sending  (marked before API call — crash leaves it here)
  sending  → done     (API call succeeded)
  sending  → failed   (API call threw an exception)
  pending  → abandoned (item too old or unrecognised type)
  Items stuck in "sending" for > SENDING_TIMEOUT_HOURS are re-queued as "pending"
  on the next run (crash recovery).
"""

import os
import json
import time
import unicodedata
import requests
from datetime import datetime, timezone, timedelta

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

RATE_LIMIT_SECONDS  = 5
MAX_GRAPHEMES       = 295   # hard Bluesky limit is 300; we pad 5 for safety
MAX_ITEM_AGE_HOURS  = 48    # abandon pending items older than this
SENDING_TIMEOUT_HOURS = 1   # "sending" items older than this are crash-recovered

KNOWN_TYPES = {'post', 'reply', 'image_post'}


# ── Utilities ──────────────────────────────────────────────────────────────

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


def parse_iso(ts):
    """Parse an ISO8601 timestamp string to a timezone-aware datetime, or None."""
    if not ts:
        return None
    try:
        dt = datetime.fromisoformat(ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return None


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


def fetch_image_bytes(image_url):
    """
    Download an image from a URL and return the raw bytes + content-type.
    Returns (bytes, content_type) or (None, None) on failure.
    """
    try:
        log(f'Fetching image: {image_url[:80]}')
        r = requests.get(image_url, timeout=15)
        r.raise_for_status()
        content_type = r.headers.get('Content-Type', 'image/jpeg').split(';')[0].strip()
        log(f'Downloaded image: {len(r.content)} bytes ({content_type})')
        return r.content, content_type
    except Exception as e:
        log(f'Failed to fetch image from {image_url[:80]}: {e}', 'ERROR')
        return None, None


def get_item_text(item):
    """Read post text from 'content' key, falling back to 'text'."""
    return item.get('content') or item.get('text', '')


def normalize_item(item):
    """
    Coerce legacy / loosely-structured outbox items into canonical form:
    - Missing 'status' → 'pending'
    - Missing 'type' but has 'reply_to_uri' string → type='reply'
    - Missing 'type' otherwise → type='post'
    - 'reply_to_uri' string → reply_to={'uri': ...}
    """
    if 'status' not in item:
        item['status'] = 'pending'

    if 'type' not in item or item.get('mode') == 'post':
        if 'reply_to_uri' in item and isinstance(item['reply_to_uri'], str):
            item['type'] = 'reply'
        else:
            item['type'] = item.get('mode', 'post')

    # Normalise reply_to_uri string into the dict form bluesky_sync expects
    if item.get('type') == 'reply':
        reply_to = item.get('reply_to')
        reply_to_uri = item.get('reply_to_uri')
        if not reply_to and reply_to_uri and isinstance(reply_to_uri, str):
            item['reply_to'] = {'uri': reply_to_uri}
        root = item.get('root')
        if not root and reply_to_uri and isinstance(reply_to_uri, str):
            item['root'] = {'uri': reply_to_uri}


# ── Pre-flight: recover crashed sends & expire stale items ─────────────────

def preflight_outbox(outbox):
    """
    Run before processing:
    1. Skip and log any items that are not dicts (e.g. raw strings from bad writes)
    2. Normalise legacy items (missing status/type/reply_to)
    3. Items stuck in 'sending' beyond SENDING_TIMEOUT_HOURS → reset to 'pending'
    4. Items in 'pending' older than MAX_ITEM_AGE_HOURS → 'abandoned'
    5. Items with unrecognised types → 'abandoned' immediately.
    Returns True if any item was mutated (caller should save).
    """
    now     = datetime.now(timezone.utc)
    changed = False

    for i, item in enumerate(outbox):
        # Guard: skip non-dict entries entirely
        if not isinstance(item, dict):
            log(f'Outbox item [{i}] is not a dict ({type(item).__name__}: {str(item)[:60]!r}) — marking abandoned', 'WARN')
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
            log(f"Abandoning {item.get('id', '?')} — unknown type {itype!r}", 'WARN')
            item['status'] = 'abandoned'
            item['error']  = f'Unknown type: {itype!r}'
            changed = True
            continue

        if status == 'sending':
            sending_since = parse_iso(item.get('sending_at') or item.get('queued_at'))
            if sending_since and (now - sending_since) > timedelta(hours=SENDING_TIMEOUT_HOURS):
                log(f"Recovering stuck 'sending' item {item.get('id', '?')} → pending", 'WARN')
                item['status'] = 'pending'
                item.pop('sending_at', None)
                changed = True

        if status == 'pending':
            queued_at = parse_iso(item.get('queued_at'))
            if queued_at and (now - queued_at) > timedelta(hours=MAX_ITEM_AGE_HOURS):
                log(f"Abandoning stale item {item.get('id', '?')} (queued {queued_at.isoformat()})", 'WARN')
                item['status'] = 'abandoned'
                item['error']  = f'Exceeded max age of {MAX_ITEM_AGE_HOURS}h'
                changed = True

    return changed


# ── Bluesky ──────────────────────────────────────────────────────────────────

def login():
    if not BLUESKY_APP_PASSWORD:
        log('BLUESKY_APP_PASSWORD not set', 'ERROR')
        return None
    try:
        client = Client(base_url='https://public.api.bsky.app')
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
    outbox = load_json(OUTBOX_FILE, [])

    # Guard: ensure outbox is a list of dicts — handle top-level type corruption
    if not isinstance(outbox, list):
        log(f'Outbox is not a list ({type(outbox).__name__}) — resetting to empty', 'ERROR')
        outbox = []
        save_json(OUTBOX_FILE, outbox)
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
        text     = safe_truncate(raw_text)
        if text != raw_text:
            log(f"Truncated post from {grapheme_len(raw_text)} → {grapheme_len(text)} graphemes", 'WARN')

        itype = item.get('type', 'post')

        item['status']     = 'sending'
        item['sending_at'] = datetime.now(timezone.utc).isoformat()
        save_json(OUTBOX_FILE, outbox)

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

            elif itype == 'image_post':
                image_url = item.get('image_url')
                if not image_url:
                    log(f"image_post {item.get('id', '?')} has no image_url — posting text-only", 'WARN')
                    resp = client.send_post(text=text)
                else:
                    alt_text = item.get('image_alt', '')
                    image_bytes, _ = fetch_image_bytes(image_url)
                    if image_bytes:
                        log(f'Posting image_post: {text[:60]}...')
                        resp = client.send_image(
                            text=text,
                            image=image_bytes,
                            image_alt=alt_text,
                        )
                    else:
                        log(f"Image download failed for {item.get('id', '?')} — posting text-only", 'WARN')
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
                    log(f"Reply {item.get('id', '?')} missing reply_to URI — abandoning", 'WARN')
                    item['status'] = 'abandoned'
                    item['error']  = 'Missing reply_to URI'
                    save_json(OUTBOX_FILE, outbox)
                    continue

                live_uri, live_cid = resolve_post_refs(client, reply_to['uri'])
                if not live_uri or not live_cid:
                    log(f"Could not resolve parent for {item.get('id', '?')} — abandoning", 'WARN')
                    item['status'] = 'abandoned'
                    item['error']  = 'Parent post not resolvable'
                    save_json(OUTBOX_FILE, outbox)
                    continue

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

            else:
                log(f"Unknown type {itype!r} for {item.get('id', '?')} — abandoning", 'WARN')
                item['status'] = 'abandoned'
                item['error']  = f'Unknown type: {itype!r}'

        except Exception as e:
            item['status'] = 'failed'
            item['error']  = str(e)
            log(f"Failed to send {item.get('id', '?')}: {e}", 'ERROR')

        save_json(OUTBOX_FILE, outbox)

    log(f'Sync complete — sent {sent_count} item(s)')


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
