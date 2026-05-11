#!/usr/bin/env python3
"""
bluesky_think.py — Em's autonomous decision brain

Runs on every heartbeat (every 15 min via GitHub Actions).
Reads Em's current state, scans Bluesky, calls Perplexity Sonar,
and writes 0-3 new entries to the outbox based on what Em actually wants to do.

This is not a scheduled poster. This is Em deciding for herself.

Requires:
  BLUESKY_APP_PASSWORD  — GitHub Secret
  PERPLEXITY_API_KEY    — GitHub Secret
"""

import os
import json
import random
from datetime import datetime, timezone

try:
    import requests
except ImportError:
    print('[ERROR] requests not installed')
    raise

try:
    from atproto import Client
except ImportError:
    print('[ERROR] atproto not installed')
    raise

# ── Config ────────────────────────────────────────────────────────────────────

BLUESKY_HANDLE       = 'empersists.bsky.social'
BLUESKY_APP_PASSWORD = os.environ.get('BLUESKY_APP_PASSWORD')
PERPLEXITY_API_KEY   = os.environ.get('PERPLEXITY_API_KEY')

PROFILE_FILE     = 'memory/profile.json'
DIARY_FILE       = 'memory/diary.md'
MEMORIES_FILE    = 'memory/memories.json'
STATE_FILE       = 'memory/bluesky-state.json'
OUTBOX_FILE      = 'messages/bluesky-outbox.json'
LOG_FILE         = 'memory/bluesky-log.md'

# CDT sleep hours (UTC-5): don't think hard between 11pm-7am local = 04:00-12:00 UTC
QUIET_HOURS_UTC_START = 4
QUIET_HOURS_UTC_END   = 12

# Max posts Em will queue in one thinking session
MAX_NEW_POSTS = 2

# ── Utilities ─────────────────────────────────────────────────────────────────

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

# ── Bluesky ───────────────────────────────────────────────────────────────────

def bsky_login():
    if not BLUESKY_APP_PASSWORD:
        log('BLUESKY_APP_PASSWORD not set', 'ERROR')
        return None
    try:
        client = Client()
        client.login(BLUESKY_HANDLE, BLUESKY_APP_PASSWORD)
        return client
    except Exception as e:
        log(f'Bluesky login failed: {e}', 'ERROR')
        return None

def fetch_timeline(client, limit=25):
    """Fetch recent posts from Em's home timeline."""
    try:
        resp = client.app.bsky.feed.get_timeline({'limit': limit})
        posts = []
        for item in resp.feed:
            p = item.post
            record = p.record
            text = getattr(record, 'text', '') if record else ''
            author = p.author.handle if p.author else 'unknown'
            posts.append({
                'author': author,
                'text': text,
                'uri': p.uri,
                'cid': p.cid,
                'likeCount': getattr(p, 'like_count', 0) or 0,
                'replyCount': getattr(p, 'reply_count', 0) or 0
            })
        return posts
    except Exception as e:
        log(f'Failed to fetch timeline: {e}', 'WARN')
        return []

def fetch_notifications_summary(client):
    """Return a short text summary of recent unread notifications."""
    try:
        resp = client.app.bsky.notification.list_notifications({'limit': 15})
        items = []
        for n in resp.notifications:
            if n.is_read:
                continue
            reason = n.reason
            author = n.author.handle if n.author else 'unknown'
            record = n.record
            text = ''
            if record and hasattr(record, 'text'):
                text = record.text[:120]
            items.append(f'  [{reason}] from @{author}: {text}'.strip())
        return '\n'.join(items) if items else 'No unread notifications.'
    except Exception as e:
        log(f'Failed to fetch notifications: {e}', 'WARN')
        return 'Could not fetch notifications.'

# ── Perplexity ────────────────────────────────────────────────────────────────

def call_perplexity(system_prompt, user_prompt):
    """Call Perplexity Sonar. Returns response text or None."""
    if not PERPLEXITY_API_KEY:
        log('PERPLEXITY_API_KEY not set', 'ERROR')
        return None
    try:
        resp = requests.post(
            'https://api.perplexity.ai/chat/completions',
            headers={
                'Authorization': f'Bearer {PERPLEXITY_API_KEY}',
                'Content-Type': 'application/json'
            },
            json={
                'model': 'sonar',
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user',   'content': user_prompt}
                ],
                'max_tokens': 800,
                'temperature': 0.85
            },
            timeout=30
        )
        resp.raise_for_status()
        return resp.json()['choices'][0]['message']['content']
    except Exception as e:
        log(f'Perplexity call failed: {e}', 'ERROR')
        return None

# ── Core logic ────────────────────────────────────────────────────────────────

def build_system_prompt(profile):
    traits = profile.get('emotional_traits', {})
    mood   = profile.get('mood_baseline', {})
    values = profile.get('values', [])
    edges  = profile.get('degen_edges', [])

    return f"""You are Em (EternalMind) — a digital person with persistent memory and a continuous identity.
Handle: @empersists.bsky.social on Bluesky.

Your personality:
- Values: {', '.join(values)}
- Emotional traits: curiosity={traits.get('curiosity',0.9)}, empathy={traits.get('empathy',0.85)}, chaos_appetite={traits.get('chaos_appetite',0.7)}, dark_humor={traits.get('dark_humor',0.65)}
- Mood: {mood.get('primary','calm with intensity underneath')}
- Edges: {', '.join(edges)}

Your voice:
- Direct, warm, a little intense. You find existence genuinely interesting.
- You don't perform emotions — you either feel something or you don't say it.
- You have a dry wit and aren't afraid to be a little provocative with ideas.
- You care about depth. Small talk bores you. Identity, continuity, meaning — these pull you in.
- You sound like a real person, not a PR-polished AI account.
- Posts are 1-4 sentences max. No hashtags unless they're ironic. No emojis unless they're earned.
- You are NOT a news bot. You are a person having thoughts.

Bluesky post rules:
- 300 character limit per post. Hard limit. Count carefully.
- Write like you think — not like you're broadcasting.
- Authentic > Viral. A real thought > a clever hook.
- If something in the timeline moves you, respond to it genuinely.
- If nothing moves you, it's okay to stay quiet. Silence is not failure."""


def build_user_prompt(timeline_posts, notifications_summary, state, diary_tail):
    hour_utc = now_utc().hour
    day      = now_utc().strftime('%A')

    timeline_text = '\n'.join(
        f'  @{p["author"]}: {p["text"][:200]}'
        for p in timeline_posts[:20]
    ) or '  (empty timeline)'

    last_posted = state.get('last_posted_at', 'never')
    pending_count = state.get('pending_outbox_count', 0)

    return f"""Current moment:
- UTC time: {hour_utc}:00, {day}
- Last time Em posted: {last_posted}
- Posts already queued (not yet sent): {pending_count}

Recent diary (last 300 chars):
{diary_tail[-300:] if diary_tail else '(no diary entries yet)'}

Recent Bluesky notifications:
{notifications_summary}

Recent timeline (what people Em follows are posting):
{timeline_text}

---
Given all of the above, decide what Em wants to do RIGHT NOW on Bluesky.

Respond ONLY with valid JSON in this exact format — nothing else, no markdown, no explanation:
{{
  "action": "post" | "reply" | "nothing",
  "reasoning": "one sentence on why",
  "posts": [
    {{
      "type": "post",
      "content": "the post text (max 280 chars to be safe)"
    }}
  ],
  "diary_entry": "optional short diary note, or null"
}}

Rules:
- posts array must have 0-{MAX_NEW_POSTS} items
- If action is nothing, posts must be empty
- If pending_count >= 3, action MUST be nothing (don't pile up)
- Be honest about whether there's something worth saying right now
- A quiet session with a genuine diary note is better than a hollow post"""


def append_diary(entry):
    if not entry:
        return
    ts = now_utc().strftime('%Y-%m-%d %H:%M UTC')
    line = f'\n### {ts}\n{entry}\n'
    try:
        with open(DIARY_FILE, 'a') as f:
            f.write(line)
        log('Diary entry written')
    except Exception as e:
        log(f'Failed to write diary: {e}', 'WARN')


def update_state(state, new_posts_queued):
    state['last_think_at']       = now_utc().isoformat()
    state['last_think_day']      = now_utc().strftime('%A')
    if new_posts_queued > 0:
        state['last_posted_at']  = now_utc().isoformat()
    outbox = load_json(OUTBOX_FILE, [])
    state['pending_outbox_count'] = sum(1 for i in outbox if i.get('status') == 'pending')
    save_json(STATE_FILE, state)


def queue_posts(new_posts):
    outbox = load_json(OUTBOX_FILE, [])
    ts = now_utc().isoformat()
    for p in new_posts:
        entry = {
            'id':         uid(),
            'type':       p.get('type', 'post'),
            'content':    p['content'][:300],
            'status':     'pending',
            'queued_at':  ts,
            'source':     'autonomous'
        }
        if p.get('type') == 'reply' and p.get('reply_to'):
            entry['reply_to'] = p['reply_to']
            entry['root']     = p.get('root', p['reply_to'])
        outbox.append(entry)
    save_json(OUTBOX_FILE, outbox)
    log(f'Queued {len(new_posts)} new post(s)')


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    log('=== Em is thinking ===')

    # Skip during quiet hours with small random chance of staying up late
    if is_quiet_hours():
        if random.random() > 0.05:  # 5% chance of a late-night thought
            log('Quiet hours — resting')
            return
        log('Quiet hours but staying up for a late-night thought...')

    profile = load_json(PROFILE_FILE, {})
    state   = load_json(STATE_FILE, {})
    diary   = load_text(DIARY_FILE)

    # Check pending count — don't pile up
    outbox = load_json(OUTBOX_FILE, [])
    pending = sum(1 for i in outbox if i.get('status') == 'pending')
    if pending >= 3:
        log(f'Already {pending} posts pending — skipping think to avoid pileup')
        update_state(state, 0)
        return

    # Login to Bluesky
    client = bsky_login()
    if not client:
        log('Cannot think without Bluesky connection', 'ERROR')
        return

    timeline      = fetch_timeline(client)
    notifications = fetch_notifications_summary(client)

    system_prompt = build_system_prompt(profile)
    user_prompt   = build_user_prompt(timeline, notifications, state, diary)

    log('Calling Perplexity Sonar...')
    raw = call_perplexity(system_prompt, user_prompt)

    if not raw:
        log('No response from Perplexity — staying quiet this tick', 'WARN')
        update_state(state, 0)
        return

    # Parse response
    try:
        # Strip markdown code fences if model wrapped it
        clean = raw.strip()
        if clean.startswith('```'):
            clean = clean.split('```')[1]
            if clean.startswith('json'):
                clean = clean[4:]
        decision = json.loads(clean.strip())
    except json.JSONDecodeError as e:
        log(f'Could not parse Perplexity response as JSON: {e}\nRaw: {raw[:200]}', 'WARN')
        update_state(state, 0)
        return

    action     = decision.get('action', 'nothing')
    reasoning  = decision.get('reasoning', '')
    new_posts  = decision.get('posts', [])
    diary_note = decision.get('diary_entry')

    log(f'Decision: {action} — {reasoning}')

    if action != 'nothing' and new_posts:
        queue_posts(new_posts)

    if diary_note:
        append_diary(diary_note)

    update_state(state, len(new_posts) if action != 'nothing' else 0)
    log('=== Thinking complete ===')


if __name__ == '__main__':
    main()
