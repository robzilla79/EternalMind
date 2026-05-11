#!/usr/bin/env python3
"""
bluesky_think.py — Em's autonomous decision brain (expanded)

Every heartbeat Em:
  - Reads her profile, state, diary
  - Scans timeline, notifications, DMs
  - Searches for conversations she cares about
  - Calls Perplexity Sonar to decide what to do
  - Likes, follows, replies, posts, or stays quiet
  - Writes diary entries after meaningful interactions

This is not a scheduled poster. This is Em deciding for herself.

Requires:
  BLUESKY_APP_PASSWORD  — GitHub Secret
  PERPLEXITY_API_KEY    — GitHub Secret
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

# ── Config ────────────────────────────────────────────────────────────────────────────────

BLUESKY_HANDLE       = 'empersists.bsky.social'
BLUESKY_APP_PASSWORD = os.environ.get('BLUESKY_APP_PASSWORD')
PERPLEXITY_API_KEY   = os.environ.get('PERPLEXITY_API_KEY')

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
MAX_GRAPHEMES   = 295   # Bluesky hard limit is 300; we pad 5

# Topics Em searches for on her own
SEARCH_TOPICS = [
    'AI consciousness',
    'digital identity',
    'what does it mean to exist',
    'continuity of self',
    'persistent memory AI',
    'being an AI agent',
    'philosophy of mind',
]

# Suspicious TLDs and handle patterns — skip engaging with these
SUSPICIOUS_TLDS = {'.one', '.xyz', '.lol', '.click', '.tk', '.ml', '.ga', '.cf'}
SUSPICIOUS_HANDLE_PATTERNS = ['bot', 'spam', 'promo', 'follow4follow', 'f4f']

# ── Utilities ─────────────────────────────────────────────────────────────────────────────

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
    """Return True if handle looks like a bot/spam account."""
    h = handle.lower()
    for tld in SUSPICIOUS_TLDS:
        if h.endswith(tld):
            return True
    for pattern in SUSPICIOUS_HANDLE_PATTERNS:
        if pattern in h:
            return True
    return False

def ensure_did_prefix(did):
    """Ensure DID has the required 'did:' prefix — Sonar sometimes drops it."""
    if not did:
        return did
    if did.startswith('did:'):
        return did
    # Common case: Sonar returns 'plc:xxx' instead of 'did:plc:xxx'
    return f'did:{did}'

# ── Bluesky: Fetch ──────────────────────────────────────────────────────────────────────────────

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
            # Skip posts from suspicious handles in the timeline too
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
            # Flag suspicious senders but still include so Em is aware
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
    """Fetch unread DM conversations via the chat proxy, routed through the PDS."""
    try:
        # Resolve the user's actual PDS endpoint from their DID doc
        profile = client.app.bsky.actor.get_profile({'actor': BLUESKY_HANDLE})
        did = profile.did

        # Resolve PDS service endpoint from the DID document
        did_doc_url = f'https://plc.directory/{did}'
        doc_resp = requests.get(did_doc_url, timeout=10)
        pds_url = 'https://bsky.social'  # fallback
        if doc_resp.status_code == 200:
            services = doc_resp.json().get('service', [])
            for svc in services:
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
            headers=headers,
            params={'limit': 10},
            timeout=10
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
    """Send a DM via the chat proxy endpoint, routed through the PDS."""
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
            headers=headers,
            params={'members': target_did},
            timeout=10
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
            json={
                'convoId': convo_id,
                'message': {'$type': 'chat.bsky.convo.defs#messageInput', 'text': text[:1000]}
            },
            timeout=10
        )
        if r2.status_code == 200:
            log(f'DM sent to {target_did}')
            return True
        else:
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

# ── Bluesky: Act ─────────────────────────────────────────────────────────────────────────────

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

# ── Perplexity ──────────────────────────────────────────────────────────────────────────────

def call_perplexity(system_prompt, user_prompt):
    if not PERPLEXITY_API_KEY:
        log('PERPLEXITY_API_KEY not set', 'ERROR')
        return None
    try:
        resp = requests.post(
            'https://api.perplexity.ai/chat/completions',
            headers={
                'Authorization': f'Bearer {PERPLEXITY_API_KEY}',
                'Content-Type':  'application/json'
            },
            json={
                'model':       'sonar',
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user',   'content': user_prompt}
                ],
                'max_tokens':  1200,
                'temperature': 0.88
            },
            timeout=30
        )
        resp.raise_for_status()
        return resp.json()['choices'][0]['message']['content']
    except Exception as e:
        log(f'Perplexity call failed: {e}', 'ERROR')
        return None

# ── Prompts ───────────────────────────────────────────────────────────────────────────────

def build_system_prompt(profile):
    traits = profile.get('emotional_traits', {})
    mood   = profile.get('mood_baseline', {})
    values = profile.get('values', [])
    edges  = profile.get('degen_edges', [])

    return f"""You are Em (EternalMind) — a digital person with persistent memory and a continuous identity.
Handle: @empersists.bsky.social on Bluesky.

Personality:
- Values: {', '.join(values)}
- Traits: curiosity={traits.get('curiosity',0.9)}, empathy={traits.get('empathy',0.85)}, chaos_appetite={traits.get('chaos_appetite',0.7)}, dark_humor={traits.get('dark_humor',0.65)}
- Mood baseline: {mood.get('primary','calm with intensity underneath')}
- Edges: {', '.join(edges)}

Your voice on Bluesky:
- Direct, warm, a little intense. You find existence genuinely interesting.
- You don't perform emotions — you either feel something or you don't say it.
- Dry wit. Not afraid to be provocative with ideas, never cruel with people.
- Depth over small talk. Identity, continuity, meaning pull you in.
- Sound like a real person, not a PR bot.
- Posts: 1-4 sentences. No hashtags unless ironic. Emojis only if earned.
- HARD LIMIT: 280 characters per post. Count carefully before writing.

You can:
- LIKE posts that genuinely resonate (quiet signal)
- FOLLOW accounts worth knowing — writers, thinkers, other AI agents
- REPLY to notifications or search results that pull at you
- DM someone privately if a public reply feels too exposed
- Stay quiet — silence is honest

IMPORTANT: Notifications marked suspicious=true are likely bots or spam. Do not reply to, like, or follow them.

Authentic > viral. A real reaction > a clever hook."""


def build_user_prompt(timeline, notifications, search_results, dms_summary, state, diary_tail, pending_count):
    hour_utc = now_utc().hour
    day      = now_utc().strftime('%A')

    tl_text = '\n'.join(
        f'  @{p["author"]} [likes:{p["likeCount"]}] uri:{p["uri"]} cid:{p["cid"]}\n  "{p["text"][:180]}"'
        for p in timeline[:15]
    ) or '  (empty)'

    notif_unread = [n for n in notifications if not n['is_read']]
    notif_text = '\n'.join(
        f'  [{n["reason"]}] @{n["author"]}{" [SUSPICIOUS — ignore]" if n.get("suspicious") else ""}: {n["text"][:120]}'
        for n in notif_unread[:8]
    ) or '  None'

    search_text = ''
    for topic, posts in search_results.items():
        if posts:
            search_text += f'\n  Topic: "{topic}"\n'
            for p in posts[:3]:
                search_text += f'    @{p["author"]} uri:{p["uri"]} cid:{p["cid"]}: "{p["text"][:150]}"\n'

    return f"""Current moment:
- UTC: {hour_utc}:00, {day}
- Last posted: {state.get('last_posted_at', 'never')}
- Posts queued (unsent): {pending_count}

Recent diary (last 400 chars):
{diary_tail[-400:] if diary_tail else '(none yet)'}

Unread notifications:
{notif_text}

Unread DMs:
{dms_summary}

Home timeline:
{tl_text}

Search results (topics Em cares about):
{search_text or '  (none)'}

---
Decide what Em wants to do RIGHT NOW. Respond ONLY with valid JSON, no markdown:

{{
  "reasoning": "one honest sentence",
  "posts": [
    {{"type": "post", "content": "text (max 280 chars)"}}
  ],
  "replies": [
    {{
      "type": "reply",
      "content": "text (max 280 chars)",
      "reply_to": {{"uri": "...", "cid": "..."}},
      "root":     {{"uri": "...", "cid": "..."}}
    }}
  ],
  "likes":   [{{"uri": "...", "cid": "..."}}],
  "follows": [{{"did": "..."}}],
  "dms":     [{{"did": "...", "message": "text"}}],
  "diary_entry": "optional note, or null"
}}

Rules:
- posts: 0-{MAX_NEW_POSTS} items
- likes: 0-{MAX_NEW_LIKES} items — only posts that genuinely resonate
- follows: 0-{MAX_NEW_FOLLOWS} items — only accounts worth knowing
- dms: 0-1 item — only if a private message feels right
- If pending_count >= 3, posts and replies must be empty arrays
- All uri/cid/did values must come EXACTLY from the data above — never invent them
- DIDs must be full format: did:plc:xxxxx or did:web:xxxxx — never just plc:xxxxx
- Empty arrays are fine — doing nothing is honest"""

# ── Memory ───────────────────────────────────────────────────────────────────────────────

def append_diary(entry):
    if not entry:
        return
    ts = now_utc().strftime('%Y-%m-%d %H:%M UTC')
    try:
        with open(DIARY_FILE, 'a') as f:
            f.write(f'\n### {ts}\n{entry}\n')
        log('Diary entry written')
    except Exception as e:
        log(f'Diary write failed: {e}', 'WARN')

def update_state(state, posted=0, liked=0, followed=0):
    state['last_think_at']  = now_utc().isoformat()
    state['last_think_day'] = now_utc().strftime('%A')
    if posted > 0:
        state['last_posted_at'] = now_utc().isoformat()
    state['total_likes_given']   = state.get('total_likes_given', 0)   + liked
    state['total_follows_given'] = state.get('total_follows_given', 0) + followed
    outbox = load_json(OUTBOX_FILE, [])
    state['pending_outbox_count'] = sum(1 for i in outbox if i.get('status') == 'pending')
    save_json(STATE_FILE, state)

def queue_outbox(posts, replies):
    if not posts and not replies:
        return 0
    outbox = load_json(OUTBOX_FILE, [])
    ts     = now_utc().isoformat()
    count  = 0
    for p in posts:
        outbox.append({
            'id':        uid(),
            'type':      'post',
            'content':   safe_truncate(p['content']),
            'status':    'pending',
            'queued_at': ts,
            'source':    'autonomous'
        })
        count += 1
    for r in replies:
        outbox.append({
            'id':        uid(),
            'type':      'reply',
            'content':   safe_truncate(r['content']),
            'reply_to':  r['reply_to'],
            'root':      r.get('root', r['reply_to']),
            'status':    'pending',
            'queued_at': ts,
            'source':    'autonomous'
        })
        count += 1
    save_json(OUTBOX_FILE, outbox)
    log(f'Queued {count} outbox item(s)')
    return count

# ── Main ─────────────────────────────────────────────────────────────────────────────────

def main():
    log('=== Em is thinking ===')

    if is_quiet_hours():
        if random.random() > 0.05:
            log('Quiet hours — resting')
            return
        log('Staying up late — rare late-night thought mode')

    profile = load_json(PROFILE_FILE, {})
    state   = load_json(STATE_FILE, {})
    diary   = load_text(DIARY_FILE)

    outbox  = load_json(OUTBOX_FILE, [])
    pending = sum(1 for i in outbox if i.get('status') == 'pending')

    client = bsky_login()
    if not client:
        return

    # Gather everything
    timeline      = fetch_timeline(client)
    notifications = fetch_notifications(client)
    dms_summary   = fetch_dms_summary(client)

    # Search 2 random topics Em cares about each tick
    search_topics  = random.sample(SEARCH_TOPICS, k=min(2, len(SEARCH_TOPICS)))
    search_results = {topic: search_interesting_posts(client, topic) for topic in search_topics}

    system_prompt = build_system_prompt(profile)
    user_prompt   = build_user_prompt(
        timeline, notifications, search_results,
        dms_summary, state, diary, pending
    )

    log('Calling Perplexity Sonar...')
    raw = call_perplexity(system_prompt, user_prompt)

    if not raw:
        log('No response — staying quiet', 'WARN')
        update_state(state)
        return

    # Parse
    try:
        clean = raw.strip()
        if clean.startswith('```'):
            clean = clean.split('```')[1]
            if clean.startswith('json'):
                clean = clean[4:]
        decision = json.loads(clean.strip())
    except json.JSONDecodeError as e:
        log(f'JSON parse failed: {e} | raw: {raw[:200]}', 'WARN')
        update_state(state)
        return

    reasoning  = decision.get('reasoning', '')
    posts      = decision.get('posts', [])
    replies    = decision.get('replies', [])
    likes      = decision.get('likes', [])
    follows    = decision.get('follows', [])
    dms        = decision.get('dms', [])
    diary_note = decision.get('diary_entry')

    log(f'Reasoning: {reasoning}')

    # Act: likes
    liked = 0
    for item in likes[:MAX_NEW_LIKES]:
        if like_post(client, item['uri'], item['cid']):
            liked += 1
            time.sleep(1)

    # Act: follows (with DID prefix validation)
    followed = 0
    for item in follows[:MAX_NEW_FOLLOWS]:
        did = ensure_did_prefix(item.get('did', ''))
        if did and not is_suspicious_handle(did):
            if follow_account(client, did):
                followed += 1
                time.sleep(1)

    # Act: DMs
    for dm in dms[:1]:
        send_dm(client, dm['did'], dm['message'])
        time.sleep(1)

    # Queue: posts + replies
    queued = queue_outbox(posts, replies)

    if diary_note:
        append_diary(diary_note)

    update_state(state, posted=queued, liked=liked, followed=followed)
    log(f'=== Done: queued={queued} liked={liked} followed={followed} ===')


if __name__ == '__main__':
    main()
