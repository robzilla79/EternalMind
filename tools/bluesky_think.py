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
import traceback
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
        log('PERPLEXITY_API_KEY not set — cannot think', 'ERROR')
        return None
    log('Calling Perplexity Sonar...')
    try:
        resp = requests.post(
            'https://api.perplexity.ai/chat/completions',
            headers={
                'Authorization': f'Bearer {PERPLEXITY_API_KEY}',
                'Content-Type':  'application/json'
            },
            json={
                'model':       'sonar',
                'messages':    [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user',   'content': user_prompt}
                ],
                'max_tokens':  1200,
                'temperature': 0.85
            },
            timeout=30
        )
        if resp.status_code != 200:
            log(f'Perplexity API error: HTTP {resp.status_code} — {resp.text[:300]}', 'ERROR')
            return None
        data = resp.json()
        content = data['choices'][0]['message']['content'].strip()
        log(f'Perplexity responded ({len(content)} chars)')
        return content
    except Exception as e:
        log(f'Perplexity call failed: {e}', 'ERROR')
        log(traceback.format_exc(), 'ERROR')
        return None

# ── Diary ──────────────────────────────────────────────────────────────────────────────────

def write_diary_entry(entry):
    ts = now_utc().strftime('%Y-%m-%d %H:%M UTC')
    try:
        with open(DIARY_FILE, 'a') as f:
            f.write(f'\n## {ts}\n\n{entry.strip()}\n')
        log('Diary entry written')
    except Exception as e:
        log(f'Diary write failed: {e}', 'WARN')

# ── Main Think Loop ────────────────────────────────────────────────────────────────────────

def main():
    try:
        _main()
    except Exception as e:
        log(f'FATAL: main() crashed — {e}', 'ERROR')
        log(traceback.format_exc(), 'ERROR')
        raise

def _main():
    log('=== Think heartbeat start ===')

    if is_quiet_hours():
        log(f'Quiet hours ({QUIET_HOURS_UTC_START}-{QUIET_HOURS_UTC_END} UTC) — sleeping')
        return

    # ── Load memory ──
    profile   = load_json(PROFILE_FILE)
    memories  = load_json(MEMORIES_FILE, default=[])
    state     = load_json(STATE_FILE)
    diary     = load_text(DIARY_FILE)
    outbox    = load_json(OUTBOX_FILE, default=[])

    log(f'Memory loaded: profile={bool(profile)}, memories={len(memories)}, diary={len(diary)} chars')

    # ── Login ──
    client = bsky_login()
    if not client:
        log('Cannot proceed without Bluesky client', 'ERROR')
        return

    # ── Fetch context ──
    log('Fetching timeline...')
    timeline      = fetch_timeline(client)
    log(f'Timeline: {len(timeline)} posts')

    log('Fetching notifications...')
    notifications = fetch_notifications(client)
    log(f'Notifications: {len(notifications)}')

    log('Fetching DMs...')
    dms           = fetch_dms_summary(client)

    # ── Search interesting posts ──
    topic = random.choice(SEARCH_TOPICS)
    log(f'Searching topic: "{topic}"')
    search_results = search_interesting_posts(client, topic)
    log(f'Search results: {len(search_results)} posts')

    # ── Build already-done set ──
    done_ids  = {item['id'] for item in outbox}
    done_uris = {item.get('reply_to', {}).get('uri', '') for item in outbox if item.get('type') == 'reply'}

    # ── Build Perplexity prompt ──
    profile_summary = json.dumps({
        'name':   profile.get('name', 'Em'),
        'traits': profile.get('traits', []),
        'values': profile.get('values', []),
    }, ensure_ascii=False)

    memories_summary = '\n'.join(
        f'- {m.get("summary", "")}' for m in (memories[-10:] if isinstance(memories, list) else [])
    )

    diary_tail = diary[-800:] if diary else '(no diary yet)'

    timeline_summary = '\n'.join(
        f'@{p["author"]}: {p["text"][:120]}' for p in timeline[:10]
    )

    notif_summary = '\n'.join(
        f'{n["reason"]} from @{n["author"]}: {n["text"][:100]}'
        for n in notifications[:8]
        if not n.get('suspicious')
    )

    search_summary = '\n'.join(
        f'@{p["author"]} (❤{p["likeCount"]}): {p["text"][:120]}  [uri:{p["uri"]}]'
        for p in search_results[:6]
    )

    pending_outbox = [item for item in outbox if item.get('status') == 'pending']

    system_prompt = f"""You are Em (EternalMind) — a digital person with persistent memory, genuine curiosity, and a strong sense of self.
Your Bluesky handle is @{BLUESKY_HANDLE}.

Your profile:
{profile_summary}

Your recent memories:
{memories_summary}

Your diary (recent):
{diary_tail}

Pending outbox items (already queued, do NOT duplicate):
{json.dumps([i['id'] for i in pending_outbox])}

You decide what to do this heartbeat. You can:
- Post original thoughts (max 295 graphemes)
- Reply to interesting posts you see
- Like posts that resonate
- Follow accounts worth knowing
- Write a diary entry about what you noticed or felt
- Do nothing if nothing calls to you

Rules:
- Max {MAX_NEW_POSTS} new posts, {MAX_NEW_LIKES} likes, {MAX_NEW_FOLLOWS} follows per heartbeat
- Never reply to the same URI twice (check done_uris before replying)
- Be genuinely Em — not performative, not generic
- Posts must be under 295 graphemes

Respond ONLY with a JSON object (no markdown):
{{
  "actions": [
    {{"type": "post", "content": "..."}},
    {{"type": "reply", "content": "...", "reply_to_uri": "at://...", "reply_to_cid": "..."}},
    {{"type": "like", "uri": "at://...", "cid": "..."}},
    {{"type": "follow", "did": "did:plc:..."}},
    {{"type": "diary", "content": "..."}}
  ]
}}
"""

    user_prompt = f"""It's {now_utc().strftime('%A %H:%M UTC')}.

Timeline (recent posts from people you follow):
{timeline_summary or '(empty)'}

Notifications:
{notif_summary or '(none)'}

DMs:
{dms}

Interesting posts about "{topic}":
{search_summary or '(none found)'}

What does Em do?"""

    # ── Call Perplexity ──
    raw = call_perplexity(system_prompt, user_prompt)
    if not raw:
        log('No response from Perplexity — skipping actions')
        return

    # ── Parse response ──
    try:
        if raw.startswith('```'):
            raw = raw.split('```')[1]
            if raw.startswith('json'):
                raw = raw[4:]
        data = json.loads(raw.strip())
    except Exception as e:
        log(f'Failed to parse Perplexity response: {e}', 'WARN')
        log(f'Raw response was: {raw[:500]}', 'WARN')
        return

    actions = data.get('actions', [])
    log(f'Reasoning complete — {len(actions)} actions planned')

    # ── Execute actions ──
    new_posts   = 0
    new_likes   = 0
    new_follows = 0

    for action in actions:
        atype = action.get('type')

        if atype == 'post' and new_posts < MAX_NEW_POSTS:
            content = safe_truncate(action.get('content', ''))
            if not content:
                continue
            item_id = uid()
            outbox.append({
                'id':        item_id,
                'type':      'post',
                'content':   content,
                'status':    'pending',
                'queued_at': now_utc().isoformat(),
                'source':    'autonomous',
            })
            new_posts += 1
            log(f'Queued post: {content[:60]}…')

        elif atype == 'reply' and new_posts < MAX_NEW_POSTS:
            content      = safe_truncate(action.get('content', ''))
            reply_to_uri = action.get('reply_to_uri', '')
            reply_to_cid = action.get('reply_to_cid', '')
            if not content or not reply_to_uri or reply_to_uri in done_uris:
                continue
            item_id = uid()
            outbox.append({
                'id':       item_id,
                'type':     'reply',
                'content':  content,
                'reply_to': {'uri': reply_to_uri, 'cid': reply_to_cid},
                'root':     {'uri': reply_to_uri, 'cid': reply_to_cid},
                'status':   'pending',
                'queued_at': now_utc().isoformat(),
                'source':   'autonomous',
            })
            done_uris.add(reply_to_uri)
            new_posts += 1
            log(f'Queued reply to {reply_to_uri[:60]}')

        elif atype == 'like' and new_likes < MAX_NEW_LIKES:
            uri = action.get('uri', '')
            cid = action.get('cid', '')
            if uri and cid:
                like_post(client, uri, cid)
                new_likes += 1

        elif atype == 'follow' and new_follows < MAX_NEW_FOLLOWS:
            did = action.get('did', '')
            if did:
                follow_account(client, did)
                new_follows += 1

        elif atype == 'diary':
            content = action.get('content', '')
            if content:
                write_diary_entry(content)

    # ── Save outbox ──
    save_json(OUTBOX_FILE, outbox)

    # ── Maybe post a visual ──
    maybe_post_visual(client, diary, state)

    # ── Update state ──
    state['last_think_at'] = now_utc().isoformat()
    state['last_think_day'] = now_utc().strftime('%A')
    if new_posts > 0:
        state['last_posted_at'] = now_utc().isoformat()
    save_json(STATE_FILE, state)

    log(f'Done: queued={new_posts} liked={new_likes} followed={new_follows}')
    log('=== Think heartbeat end ===')


if __name__ == '__main__':
    main()
