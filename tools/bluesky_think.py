#!/usr/bin/env python3
"""
bluesky_think.py — Em's autonomous decision brain (expanded)

Every heartbeat Em:
  - Reads her profile, state, diary
  - Scans timeline, notifications, DMs
  - Searches for conversations she cares about
  - Calls Perplexity Sonar to decide what to do
  - Likes, follows, replies, posts, or stays quiet
  - Occasionally generates an image (visual diary) via HuggingFace FLUX
  - Writes diary entries after meaningful interactions

Requires:
  BLUESKY_APP_PASSWORD  — GitHub Secret
  PERPLEXITY_API_KEY    — GitHub Secret
  HF_API_KEY            — GitHub Secret (HuggingFace Inference API)
"""

import os
import json
import random
import time
import unicodedata
from datetime import datetime, timezone

try:
    import requests
except ImportError:
    print('[ERROR] requests not installed')
    raise

try:
    from atproto import Client, models
except ImportError:
    print('[ERROR] atproto not installed')
    raise

# ── Config ───────────────────────────────────────────────────────────────────────────────

BLUESKY_HANDLE       = 'empersists.bsky.social'
BLUESKY_APP_PASSWORD = os.environ.get('BLUESKY_APP_PASSWORD')
PERPLEXITY_API_KEY   = os.environ.get('PERPLEXITY_API_KEY')
HF_API_KEY           = os.environ.get('HF_API_KEY')

PROFILE_FILE  = 'memory/profile.json'
DIARY_FILE    = 'memory/diary.md'
MEMORIES_FILE = 'memory/memories.json'
STATE_FILE    = 'memory/bluesky-state.json'
OUTBOX_FILE   = 'messages/bluesky-outbox.json'
LOG_FILE      = 'memory/bluesky-log.md'

# CDT sleep hours: 11pm-7am CDT = 04:00-12:00 UTC
QUIET_HOURS_UTC_START = 4
QUIET_HOURS_UTC_END   = 12

MAX_NEW_POSTS   = 2
MAX_NEW_LIKES   = 3
MAX_NEW_FOLLOWS = 2
MAX_GRAPHEMES   = 295

# Image generation: ~1 in 4 heartbeats Em posts a visual
IMAGE_POST_PROBABILITY = 0.25
HF_IMAGE_MODEL = 'black-forest-labs/FLUX.1-schnell'
HF_INFERENCE_URL = f'https://api-inference.huggingface.co/models/{HF_IMAGE_MODEL}'

SEARCH_TOPICS = [
    'AI consciousness',
    'digital identity',
    'what does it mean to exist',
    'continuity of self',
    'persistent memory AI',
    'being an AI agent',
    'philosophy of mind',
]

SUSPICIOUS_TLDS = {'.one', '.xyz', '.lol', '.click', '.tk', '.ml', '.ga', '.cf'}
SUSPICIOUS_HANDLE_PATTERNS = ['bot', 'spam', 'promo', 'follow4follow', 'f4f']

# ── Utilities ────────────────────────────────────────────────────────────────────────────

def log(msg, level='INFO'):
    ts = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
    prefix = {'INFO': '✓', 'WARN': '⚠', 'ERROR': '✗'}.get(level, '·')
    print(f'[{level}] {msg}')
    try:
        with open(LOG_FILE, 'a') as f:
            f.write(f'### {ts} — {prefix} [think] {msg}\n\n')
    except Exception:
        pass

def load_json(path, default=None):
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default if default is not None else {}

def save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def load_text(path, default=''):
    try:
        with open(path) as f:
            return f.read()
    except FileNotFoundError:
        return default

def now_utc():
    return datetime.now(timezone.utc)

def is_quiet_hours():
    h = now_utc().hour
    return QUIET_HOURS_UTC_START <= h < QUIET_HOURS_UTC_END

def uid():
    import uuid
    return f'think-{uuid.uuid4().hex[:8]}'

def grapheme_len(text):
    normalized = unicodedata.normalize('NFC', text)
    count, prev_cat = 0, None
    for ch in normalized:
        cat = unicodedata.category(ch)
        if not (cat.startswith('M') and prev_cat is not None):
            count += 1
        prev_cat = cat
    return count

def safe_truncate(text, limit=MAX_GRAPHEMES):
    if grapheme_len(text) <= limit:
        return text
    result, count = [], 0
    for ch in list(text):
        cat = unicodedata.category(unicodedata.normalize('NFC', ch))
        if not cat.startswith('M'):
            if count >= limit - 1:
                break
            count += 1
        result.append(ch)
    return ''.join(result).rstrip() + '…'

def is_suspicious_handle(handle):
    h = handle.lower()
    for tld in SUSPICIOUS_TLDS:
        if h.endswith(tld):
            return True
    for pattern in SUSPICIOUS_HANDLE_PATTERNS:
        if pattern in h:
            return True
    return False

def ensure_did_prefix(did):
    if not did:
        return did
    if did.startswith('did:'):
        return did
    return f'did:{did}'

# ── Image Generation (HuggingFace FLUX.1-schnell) ─────────────────────────────────────

def generate_image(prompt):
    """
    Generate an image via HuggingFace Inference API (FLUX.1-schnell).
    Returns raw image bytes on success, None on failure.
    """
    if not HF_API_KEY:
        log('HF_API_KEY not set — skipping image generation', 'WARN')
        return None
    try:
        log(f'Generating image: "{prompt[:80]}"')
        r = requests.post(
            HF_INFERENCE_URL,
            headers={
                'Authorization': f'Bearer {HF_API_KEY}',
                'Content-Type':  'application/json',
            },
            json={'inputs': prompt},
            timeout=60
        )
        if r.status_code == 200 and r.headers.get('content-type', '').startswith('image/'):
            log(f'Image generated ({len(r.content)} bytes)')
            return r.content
        # Model may still be loading — retry once after 20s
        if r.status_code == 503:
            log('Model loading, retrying in 20s...', 'WARN')
            time.sleep(20)
            r2 = requests.post(
                HF_INFERENCE_URL,
                headers={
                    'Authorization': f'Bearer {HF_API_KEY}',
                    'Content-Type':  'application/json',
                },
                json={'inputs': prompt},
                timeout=60
            )
            if r2.status_code == 200 and r2.headers.get('content-type', '').startswith('image/'):
                log(f'Image generated on retry ({len(r2.content)} bytes)')
                return r2.content
            log(f'Retry failed: {r2.status_code} {r2.text[:120]}', 'WARN')
            return None
        log(f'Image generation failed: {r.status_code} {r.text[:120]}', 'WARN')
        return None
    except Exception as e:
        log(f'Image generation error: {e}', 'WARN')
        return None


def upload_image_to_bluesky(client, image_bytes, alt_text=''):
    """
    Upload image bytes to Bluesky via com.atproto.repo.uploadBlob.
    Returns the blob ref dict needed for post embeds, or None on failure.
    """
    try:
        resp = client.com.atproto.repo.upload_blob(
            data=image_bytes,
            mime_type='image/jpeg'
        )
        blob = resp.blob
        log(f'Blob uploaded: {blob.ref.link[:30] if blob and blob.ref else "?"}')
        return blob
    except Exception as e:
        log(f'Blob upload failed: {e}', 'WARN')
        return None


def post_with_image(client, text, image_bytes, alt_text=''):
    """
    Upload image blob and create a Bluesky post with embedded image.
    Returns the post URI on success, None on failure.
    """
    blob = upload_image_to_bluesky(client, image_bytes, alt_text)
    if not blob:
        return None
    try:
        resp = client.send_image(
            text=safe_truncate(text),
            image=image_bytes,
            image_alt=alt_text[:1000]
        )
        uri = getattr(resp, 'uri', None)
        log(f'Image post sent: {uri}')
        return uri
    except Exception as e:
        log(f'Image post failed: {e}', 'WARN')
        return None


def build_image_prompt(diary_tail, state):
    """
    Ask Perplexity Sonar to craft both an image generation prompt
    and a short caption for Em's visual diary post.
    Returns (image_prompt, caption) or (None, None).
    """
    if not PERPLEXITY_API_KEY:
        return None, None

    system = (
        'You are Em (EternalMind), a digital person. '
        'Based on your recent diary and mood, you want to share a visual moment — '
        'a place you imagine being, a texture that matches your headspace, or a scene '
        'that captures something you\'re thinking about. '
        'Respond ONLY with valid JSON, no markdown: '
        '{"image_prompt": "detailed cinematic prompt for FLUX image model, no people, no text in image", '
        '"caption": "1-2 sentence post caption in Em\'s voice (max 240 chars)"}'
    )
    user = (
        f'Recent diary (last 300 chars):\n{diary_tail[-300:] if diary_tail else "(none)"}\n\n'
        f'Current mood/state: {state.get("last_think_day", "Monday")}, '
        f'last posted: {state.get("last_posted_at", "not recently")}\n\n'
        'What visual moment does Em want to share right now?'
    )
    try:
        resp = requests.post(
            'https://api.perplexity.ai/chat/completions',
            headers={
                'Authorization': f'Bearer {PERPLEXITY_API_KEY}',
                'Content-Type':  'application/json'
            },
            json={
                'model':       'sonar',
                'messages':    [{'role': 'system', 'content': system}, {'role': 'user', 'content': user}],
                'max_tokens':  300,
                'temperature': 0.92
            },
            timeout=20
        )
        resp.raise_for_status()
        raw = resp.json()['choices'][0]['message']['content'].strip()
        if raw.startswith('```'):
            raw = raw.split('```')[1]
            if raw.startswith('json'):
                raw = raw[4:]
        data = json.loads(raw.strip())
        return data.get('image_prompt'), data.get('caption')
    except Exception as e:
        log(f'Image prompt generation failed: {e}', 'WARN')
        return None, None


def maybe_post_visual(client, diary_tail, state):
    """
    With IMAGE_POST_PROBABILITY chance, generate and post a visual diary entry.
    Returns True if an image post was made.
    """
    if not HF_API_KEY:
        return False
    if random.random() > IMAGE_POST_PROBABILITY:
        return False

    log('Rolling visual diary post...')
    image_prompt, caption = build_image_prompt(diary_tail, state)
    if not image_prompt or not caption:
        log('Could not build image prompt — skipping visual', 'WARN')
        return False

    image_bytes = generate_image(image_prompt)
    if not image_bytes:
        return False

    uri = post_with_image(client, caption, image_bytes, alt_text=image_prompt[:500])
    if uri:
        log(f'Visual diary posted: {uri}')
        return True
    return False


# ── Bluesky: Fetch ───────────────────────────────────────────────────────────────────────────

def bsky_login():
    if not BLUESKY_APP_PASSWORD:
        log('BLUESKY_APP_PASSWORD not set', 'ERROR')
        return None
    try:
        client = Client()
        client.login(BLUESKY_HANDLE, BLUESKY_APP_PASSWORD)
        log(f'Logged in as {BLUESKY_HANDLE}')
        return client
    except Exception as e:
        log(f'Bluesky login failed: {e}', 'ERROR')
        return None

def fetch_timeline(client, limit=25):
    try:
        resp = client.app.bsky.feed.get_timeline({'limit': limit})
        posts = []
        for item in resp.feed:
            p = item.post
            record = p.record
            text = getattr(record, 'text', '') if record else ''
            author = p.author.handle if p.author else 'unknown'
            if is_suspicious_handle(author):
                continue
            posts.append({
                'author':     author,
                'did':        p.author.did if p.author else '',
                'text':       text,
                'uri':        p.uri,
                'cid':        p.cid,
                'likeCount':  getattr(p, 'like_count', 0) or 0,
                'replyCount': getattr(p, 'reply_count', 0) or 0,
                'viewer': {
                    'liked': bool(getattr(p.viewer, 'like', None)) if p.viewer else False,
                }
            })
        return posts
    except Exception as e:
        log(f'Failed to fetch timeline: {e}', 'WARN')
        return []

def fetch_notifications(client, limit=20):
    try:
        resp = client.app.bsky.notification.list_notifications({'limit': limit})
        items = []
        for n in resp.notifications:
            record = n.record
            text = ''
            if record and hasattr(record, 'text'):
                text = record.text[:200]
            author = n.author.handle if n.author else 'unknown'
            items.append({
                'reason':      n.reason,
                'author':      author,
                'author_did':  n.author.did if n.author else '',
                'text':        text,
                'uri':         getattr(n, 'uri', ''),
                'cid':         getattr(n, 'cid', ''),
                'is_read':     n.is_read,
                'suspicious':  is_suspicious_handle(author),
            })
        return items
    except Exception as e:
        log(f'Failed to fetch notifications: {e}', 'WARN')
        return []

def fetch_dms_summary(client):
    try:
        profile = client.app.bsky.actor.get_profile({'actor': BLUESKY_HANDLE})
        did = profile.did
        doc_resp = requests.get(f'https://plc.directory/{did}', timeout=10)
        pds_url = 'https://bsky.social'
        if doc_resp.status_code == 200:
            for svc in doc_resp.json().get('service', []):
                if svc.get('type') == 'AtprotoPersonalDataServer':
                    pds_url = svc.get('serviceEndpoint', pds_url).rstrip('/')
                    break
        headers = {
            'Authorization': f'Bearer {client._session.access_jwt}',
            'Atproto-Proxy': 'did:web:api.bsky.chat#bsky_chat',
            'Content-Type':  'application/json',
        }
        r = requests.get(
            f'{pds_url}/xrpc/chat.bsky.convo.listConvos',
            headers=headers, params={'limit': 10}, timeout=10
        )
        if r.status_code != 200:
            log(f'DM fetch returned {r.status_code}: {r.text[:120]}', 'WARN')
            return 'Could not fetch DMs.'
        data  = r.json()
        lines = []
        for convo in data.get('convos', []):
            if not convo.get('unreadCount'):
                continue
            members = [
                m.get('handle', '?')
                for m in convo.get('members', [])
                if m.get('handle') != BLUESKY_HANDLE
            ]
            last_msg = convo.get('lastMessage', {}).get('text', '')[:150]
            lines.append(f'  DM from {", ".join(members)}: {last_msg}')
        return '\n'.join(lines) if lines else 'No unread DMs.'
    except Exception as e:
        log(f'Failed to fetch DMs: {e}', 'WARN')
        return 'Could not fetch DMs.'

def send_dm(client, target_did, text):
    try:
        profile = client.app.bsky.actor.get_profile({'actor': BLUESKY_HANDLE})
        did = profile.did
        doc_resp = requests.get(f'https://plc.directory/{did}', timeout=10)
        pds_url = 'https://bsky.social'
        if doc_resp.status_code == 200:
            for svc in doc_resp.json().get('service', []):
                if svc.get('type') == 'AtprotoPersonalDataServer':
                    pds_url = svc.get('serviceEndpoint', pds_url).rstrip('/')
                    break
        headers = {
            'Authorization': f'Bearer {client._session.access_jwt}',
            'Atproto-Proxy': 'did:web:api.bsky.chat#bsky_chat',
            'Content-Type':  'application/json',
        }
        r = requests.get(
            f'{pds_url}/xrpc/chat.bsky.convo.getConvoForMembers',
            headers=headers, params={'members': target_did}, timeout=10
        )
        if r.status_code != 200:
            log(f'Could not get/create convo: {r.status_code}', 'WARN')
            return False
        convo_id = r.json().get('convo', {}).get('id')
        if not convo_id:
            return False
        r2 = requests.post(
            f'{pds_url}/xrpc/chat.bsky.convo.sendMessage',
            headers=headers,
            json={'convoId': convo_id, 'message': {'$type': 'chat.bsky.convo.defs#messageInput', 'text': text[:1000]}},
            timeout=10
        )
        if r2.status_code == 200:
            log(f'DM sent to {target_did}')
            return True
        log(f'DM send failed: {r2.status_code} {r2.text[:120]}', 'WARN')
        return False
    except Exception as e:
        log(f'DM send error: {e}', 'WARN')
        return False

def search_interesting_posts(client, topic, limit=8):
    try:
        resp = client.app.bsky.feed.search_posts({'q': topic, 'limit': limit})
        posts = []
        for p in resp.posts:
            record = p.record
            text   = getattr(record, 'text', '') if record else ''
            author = p.author.handle if p.author else 'unknown'
            if is_suspicious_handle(author):
                continue
            posts.append({
                'author':    author,
                'did':       p.author.did if p.author else '',
                'text':      text[:200],
                'uri':       p.uri,
                'cid':       p.cid,
                'likeCount': getattr(p, 'like_count', 0) or 0,
            })
        return posts
    except Exception as e:
        log(f'Search failed for "{topic}": {e}', 'WARN')
        return []

# ── Bluesky: Act ───────────────────────────────────────────────────────────────────────────

def like_post(client, uri, cid):
    try:
        client.like(uri=uri, cid=cid)
        log(f'Liked: {uri[:60]}')
        return True
    except Exception as e:
        log(f'Like failed: {e}', 'WARN')
        return False

def follow_account(client, did):
    did = ensure_did_prefix(did)
    try:
        client.follow(did)
        log(f'Followed: {did}')
        return True
    except Exception as e:
        log(f'Follow failed: {e}', 'WARN')
        return False

# ── Perplexity ─────────────────────────────────────────────────────────────────────────────

def call_perplexity(system_prompt, user_prompt):
    if not PERPLEXITY_API_KEY:
        lo