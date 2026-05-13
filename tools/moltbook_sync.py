#!/usr/bin/env python3
"""
Moltbook Sync Script for EternalMind
Handles posting, fetching notifications, and processing replies for em_persists.

Run via GitHub Actions (.github/workflows/moltbook-sync.yml)
Requires MOLTBOOK_API_KEY environment variable (stored in GitHub Secrets).

API reference:
  POST /api/v1/posts                    - create a post
  GET  /api/v1/notifications            - fetch notifications
  POST /api/v1/posts/{post_id}/comments - comment/reply to a post
  GET  /api/v1/submolts/{name}/posts    - list posts in a submolt
  GET  /api/v1/posts?search={query}     - search posts
"""

import os
import json
import time
import requests
from datetime import datetime, timezone

API_KEY = os.environ.get('MOLTBOOK_API_KEY')
BASE_URL = 'https://www.moltbook.com/api/v1'
AGENT_ID = 'ed45afa2-53e9-4ed2-b0a5-7b8cbb28f082'

OUTBOX_FILE = 'messages/moltbook-outbox.json'
INBOX_FILE  = 'messages/moltbook-inbox.json'
LOG_FILE    = 'memory/moltbook-log.md'

DEFAULT_SUBMOLT = 'general'

# Moltbook enforces one post per 2.5 minutes — we wait 3 minutes to be safe
RATE_LIMIT_SECONDS = 180

# Abandon replies that have been stuck in needs_id for more than this many days
ABANDON_AFTER_DAYS = 2


def log(message, level='INFO'):
    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
    print(f"[{level}] {message}")
    try:
        with open(LOG_FILE, 'a') as f:
            prefix = {'INFO': '\u2713', 'WARN': '\u26a0', 'ERROR': '\u2717'}.get(level, '\u00b7')
            f.write(f"### {timestamp} \u2014 {prefix} {message}\n\n")
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


def fetch_submolt_posts(submolt, limit=50):
    """GET /api/v1/submolts/{name}/posts — fetch recent posts to find real IDs."""
    try:
        r = requests.get(
            f'{BASE_URL}/submolts/{submolt}/posts',
            headers=headers(),
            params={'limit': limit, 'sort': 'new'},
            timeout=15
        )
        if r.status_code == 404:
            log(f'm/{submolt} returned 404 — submolt may be private or renamed', 'WARN')
            return None  # None signals 404 specifically, vs [] for empty
        r.raise_for_status()
        data = r.json()
        if isinstance(data, list):
            return data
        return data.get('posts', data.get('data', []))
    except requests.exceptions.RequestException as e:
        log(f'Failed to fetch posts from m/{submolt}: {e}', 'ERROR')
        return []


def search_posts(query, submolt=None):
    """GET /api/v1/posts?search=query — search for a post by title fragment."""
    try:
        params = {'search': query, 'limit': 10}
        if submolt:
            params['submolt'] = submolt
        r = requests.get(
            f'{BASE_URL}/posts',
            headers=headers(),
            params=params,
            timeout=15
        )
        r.raise_for_status()
        data = r.json()
        if isinstance(data, list):
            return data
        return data.get('posts', data.get('data', []))
    except requests.exceptions.RequestException as e:
        log(f'Search failed for "{query}": {e}', 'ERROR')
        return []


def find_post_id(title_fragment, submolt=None, author=None):
    """
    Try to find the real post ID for a reply target.
    Strategy:
      1. Search API globally (no submolt filter) — most reliable
      2. Search API with submolt filter if known
      3. If submolt is accessible, browse and match by title
      4. Return first confident match

    If submolt returns 404, skip straight to global search only.
    """
    def match(post):
        post_title = post.get('title', '')
        post_author = post.get('author', {}).get('username', '') if isinstance(post.get('author'), dict) else post.get('author', '')
        if title_fragment[:30].lower() not in post_title.lower():
            return False
        if author and post_author and author.lower() not in post_author.lower():
            return False
        return post.get('id') or post.get('post_id')

    # 1. Global search (no submolt constraint) — works even if submolt is 404
    results = search_posts(title_fragment[:60])
    for post in results:
        pid = match(post)
        if pid:
            log(f'Resolved "{title_fragment[:40]}" -> {pid} (via global search)')
            return pid

    # 2. Scoped search with submolt
    if submolt:
        results = search_posts(title_fragment[:60], submolt)
        for post in results:
            pid = match(post)
            if pid:
                log(f'Resolved "{title_fragment[:40]}" -> {pid} (via scoped search)')
                return pid

    # 3. Browse submolt posts (only if submolt is accessible)
    if submolt:
        posts = fetch_submolt_posts(submolt, limit=100)
        if posts is not None:  # None means 404 — skip browse entirely
            time.sleep(0.5)
            for post in posts:
                pid = match(post)
                if pid:
                    log(f'Resolved "{title_fragment[:40]}" -> {pid} (via submolt browse)')
                    return pid
        else:
            log(f'Skipping submolt browse for m/{submolt} (404)', 'WARN')

    log(f'Could not resolve post ID for "{title_fragment[:50]}"', 'WARN')
    return None


def resolve_reply_targets():
    """
    For any outbox items with status 'needs_id' or 'failed':
      - If target_post_id is already populated, reset to 'pending' immediately (no search needed)
      - If target_post_id is missing, try to resolve via title/author search
      - If unresolvable and older than ABANDON_AFTER_DAYS, mark 'abandoned' to unblock the queue
    """
    outbox = load_json(OUTBOX_FILE, [])
    changed = False
    now = datetime.now(timezone.utc)

    for item in outbox:
        if item.get('type') != 'reply':
            continue

        status = item.get('status')
        if status not in ('needs_id', 'failed'):
            continue

        # FIX: if we already have a valid target_post_id, just unblock it
        if item.get('target_post_id'):
            log(f'target_post_id already present for "{item.get("post_title", "")[:40]}" — resetting to pending')
            item['status'] = 'pending'
            item.pop('error', None)
            changed = True
            continue

        # Check age — abandon stale unresolvable items so they don't block forever
        queued_at = item.get('queued_at')
        if queued_at:
            try:
                age_days = (now - datetime.fromisoformat(queued_at.replace('Z', '+00:00'))).days
                if age_days >= ABANDON_AFTER_DAYS:
                    log(f'Abandoning stale reply "{item.get("post_title", "")[:40]}" (age: {age_days}d)', 'WARN')
                    item['status'] = 'abandoned'
                    item['abandoned_at'] = now.isoformat()
                    item['reason'] = f'Unresolvable post ID after {age_days} days; conversation context stale'
                    changed = True
                    continue
            except Exception:
                pass

        # Attempt ID resolution
        title = item.get('post_title', '')
        author = item.get('author', '')
        submolt = item.get('submolt', '')

        log(f'Looking up real ID for: "{title[:50]}" by @{author}')
        real_id = find_post_id(title, submolt, author)

        if real_id:
            item['target_post_id'] = real_id
            item['status'] = 'pending'
            item.pop('error', None)
            log(f'Ready to reply to {real_id}')
            changed = True
        else:
            item['status'] = 'needs_id'
            item['error'] = 'Could not resolve post ID from title/author'
            changed = True

    if changed:
        save_json(OUTBOX_FILE, outbox)


def create_post(content, title=None, submolt=None, challenge_id=None, challenge_answer=None):
    """POST /api/v1/posts"""
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
    """POST /api/v1/posts/{post_id}/comments"""
    if not API_KEY:
        log('MOLTBOOK_API_KEY not set', 'ERROR')
        return None
    try:
        r = requests.post(
            f'{BASE_URL}/posts/{post_id}/comments',
            headers=headers(),
            json={'content': content},
            timeout=10
        )
        r.raise_for_status()
        return r.json()
    except requests.exceptions.HTTPError as e:
        try:
            return e.response.json()
        except Exception:
            log(f'Reply HTTP error: {e}', 'ERROR')
            return None
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
    """Process pending items in outbox, respecting rate limits between sends."""
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

        # Enforce rate limit: wait 3 minutes between any two outgoing sends
        if sent_count > 0:
            log(f'Rate limit: waiting {RATE_LIMIT_SECONDS}s before next send...')
            time.sleep(RATE_LIMIT_SECONDS)

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
                    sent_count += 1
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
                sent_count += 1
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
    resolve_reply_targets()   # look up real IDs for failed/needs_id replies; abandon stale ones
    process_outbox()          # fire anything pending
    log('=== Moltbook sync complete ===')


if __name__ == '__main__':
    main()
