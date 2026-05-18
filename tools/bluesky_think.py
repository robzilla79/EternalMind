#!/usr/bin/env python3
"""
bluesky_think.py — Em's autonomous decision brain (v2)

Every heartbeat Em:
- Reads her profile, state, diary, and metrics snapshot
- Scans timeline, notifications, DMs
- Searches for conversations she cares about
- Calls Perplexity Sonar to decide what to do
- Likes, follows, replies, quote-posts, posts, or stays quiet
- Posts selfies from bank (max 2/day) OR abstract images freely (no cap)
- Writes diary entries after meaningful interactions
- Scores last post via em_observe (private observability layer)
- Promotes self-authored memories to the queue
- Updates rolling metrics after every heartbeat

Behavior modes (set via bluesky-state.json "mode" key):
  normal      — default caps, balanced behavior
  exploration — more follows (+2), wider search, biased toward new people
  quiet       — no new posts, 2 likes max, replies to direct mentions only
  maintenance — all action caps at 0, observability layer only

Requires:
  BLUESKY_APP_PASSWORD  — GitHub Secret
  PERPLEXITY_API_KEY    — GitHub Secret
  HF_API_KEY            — GitHub Secret (optional, for live image generation)
"""

import os
import sys
import json
import random
import time
import subprocess
import traceback
import requests
from datetime import datetime, timezone, timedelta

# ── atproto ───────────────────────────────────────────────────────────────────────
try:
    from atproto import Client, models
except ImportError:
    print('[ERROR] atproto not installed')
    raise

# Add tools/ to path so em_observe and em_code can be imported
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from em_observe import observe as em_observe
except ImportError:
    em_observe = None
    print('[WARN] em_observe not available — observability disabled')

try:
    from em_code import trigger_self_repair
except ImportError:
    trigger_self_repair = None
    print('[WARN] em_code not available — self-repair disabled')

# ── Config ───────────────────────────────────────────────────────────────────────
BLUESKY_HANDLE       = os.environ.get('BLUESKY_HANDLE', 'empersists.bsky.social')
BLUESKY_APP_PASSWORD = os.environ.get('BLUESKY_APP_PASSWORD')
PERPLEXITY_API_KEY   = os.environ.get('PERPLEXITY_API_KEY')
HF_API_KEY           = os.environ.get('HF_API_KEY')

REPO_ROOT    = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
PROFILE_FILE  = os.path.join(REPO_ROOT, 'memory/profile.json')
DIARY_FILE    = os.path.join(REPO_ROOT, 'memory/diary.md')
VOICE_FILE    = os.path.join(REPO_ROOT, 'memory/em-voice-guide.md')
MEMORIES_FILE = os.path.join(REPO_ROOT, 'memory/memories.json')
STATE_FILE    = os.path.join(REPO_ROOT, 'memory/bluesky-state.json')
OUTBOX_FILE   = os.path.join(REPO_ROOT, 'messages/bluesky-outbox.json')
LOG_FILE      = os.path.join(REPO_ROOT, 'memory/bluesky-log.md')
METRICS_FILE  = os.path.join(REPO_ROOT, 'memory/metrics-snapshot.json')
MEMORY_SEARCH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'memory_search.py')

# Image bank directory (pre-generated consistent Em images)
IMAGE_BANK_DIR    = os.path.join(REPO_ROOT, 'memory/creations')
IMAGE_BANK_PREFIX = 'selfie-'

# HuggingFace image generation
HF_INFERENCE_BASE      = 'https://api-inference.huggingface.co/models'
HF_IMAGE_MODEL_PRIMARY  = 'stabilityai/stable-diffusion-xl-base-1.0'
HF_IMAGE_MODEL_FALLBACK = 'runwayml/stable-diffusion-v1-5'

# Rate limits (global defaults — overridden per-run by behavior mode)
MAX_NEW_POSTS    = 2
MAX_NEW_LIKES    = 6
MAX_NEW_FOLLOWS  = 3
MAX_FOLLOW_TOTAL = 500

MAX_SELFIES_PER_DAY  = 2
REPLY_COOLDOWN_HOURS = 6

# Valid behavior modes
VALID_MODES = {'normal', 'exploration', 'quiet', 'maintenance'}

# Em's appearance block (used in image prompts)
EM_APPEARANCE = (
    "A photorealistic portrait of a young woman in her late 20s. "
    "Dark wavy hair, loose and slightly tousled. Striking teal-green eyes. "
    "Light freckles across the nose and cheeks. Warm skin tone. "
    "Expression: thoughtful, a little intense, like she's halfway through a thought. "
    "Aesthetic: indie/intellectual — not glamorous, not corporate. Real."
)

# Search topics Em cares about — the world, people, culture, being alive
SEARCH_TOPICS = [
    "saturday night",
    "things nobody talks about",
    "what are people feeling right now",
    "this week I realized",
    "the best conversations happen",
    "something I can't stop thinking about",
    "late night thoughts",
    "what it feels like to",
    "music that hits different",
    "moments that stay with you",
    "things that make you feel alive",
    "what nobody tells you about",
    "the weird beauty of",
    "people watching",
    "city at night",
    "something shifted today",
    "I've been thinking about",
    "culture right now",
    "what makes someone interesting",
    "the feeling when",
]

SUSPICIOUS_TLDS = {'.one', '.xyz', '.lol', '.click', '.tk', '.ml', '.ga', '.cf'}
SUSPICIOUS_HANDLE_PATTERNS = ['bot', 'spam', 'promo', 'follow4follow', 'f4f']

# ── Utilities ─────────────────────────────────────────────────────────────────────

def log(msg, level='INFO'):
    ts = datetime.now(timezone.utc).strftime('%H:%M:%S')
    print(f'[{ts}] [{level}] {msg}')


def now_utc():
    return datetime.now(timezone.utc)


def load_json(path, default=None):
    try:
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default if default is not None else {}


def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_text(path, default=''):
    try:
        with open(path, encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return default


def safe_truncate(text, limit=295):
    if len(text) <= limit:
        return text
    return text[:limit - 1] + '\u2026'


def is_suspicious_handle(handle):
    h = handle.lower()
    for pat in SUSPICIOUS_HANDLE_PATTERNS:
        if pat in h:
            return True
    for tld in SUSPICIOUS_TLDS:
        if h.endswith(tld):
            return True
    return False


def is_valid_cid(cid):
    if not cid or not isinstance(cid, str):
        return False
    if len(cid) < 8:
        return False
    if cid.startswith('bafyrei') or cid.startswith('bafy') or len(cid) > 30:
        return True
    return False


def ensure_did_prefix(did):
    if did and not did.startswith('did:'):
        return f'did:plc:{did}'
    return did


def extract_named_diary_entries(diary_text, max_entries=3):
    if not diary_text:
        return '(no diary entries yet)'
    entries = []
    current = []
    for line in diary_text.split('\n'):
        if line.startswith('## '):
            if current:
                entries.append('\n'.join(current))
            current = [line]
        elif current:
            current.append(line)
    if current:
        entries.append('\n'.join(current))
    recent = entries[-max_entries:] if entries else []
    return '\n\n'.join(recent) or '(no diary entries yet)'


# ── Memory Search ──────────────────────────────────────────────────────────────

def run_memory_search(query, top_n=3):
    """
    Call memory_search.py --json for the given query.
    Returns a formatted excerpt string, or '' on failure.
    """
    try:
        result = subprocess.run(
            ['python', MEMORY_SEARCH, query, '--json'],
            capture_output=True, text=True, timeout=30,
            env={**os.environ, 'PYTHONIOENCODING': 'utf-8'}
        )
        if result.returncode != 0:
            log(f'memory_search non-zero: {result.stderr[:200]}', 'WARN')
            return ''
        hits = json.loads(result.stdout)
        if not hits:
            return ''
        lines = []
        for h in hits[:top_n]:
            source  = h.get('source', 'unknown')
            excerpt = h.get('excerpt', '').strip()
            score   = h.get('score', 0)
            lines.append(f'[{source} | {score:.3f}]\n{excerpt}')
        return '\n\n'.join(lines)
    except Exception as e:
        log(f'memory_search error: {e}', 'WARN')
        return ''


def build_memory_recall(topic):
    """
    Run a small set of memory searches seeded by the active search topic
    plus a few stable identity anchors. Returns a formatted block for
    injection into the system prompt.
    """
    queries = {
        'who I am':              'identity continuity self',
        'how I write and sound': 'voice expression writing style',
        f'thoughts on {topic}':  topic,
    }
    recall_parts = []
    for label, query in queries.items():
        result = run_memory_search(query, top_n=3)
        if result:
            recall_parts.append(f'### {label}\n{result}')
            log(f'  memory recall ✓ [{label}] ({len(result)} chars)')
        else:
            log(f'  memory recall – [{label}] (no results)')

    if not recall_parts:
        return ''

    return (
        '\u2501' * 36 + '\n'
        'WHAT YOU ALREADY KNOW (from your own memory files)\n'
        + '\u2501' * 36 + '\n'
        'These excerpts were retrieved by semantic search across your diary,\n'
        'reflections, identity docs, and memories. Build on them. Don\'t repeat\n'
        'them wholesale — use them as the foundation you\'re standing on.\n\n'
        + '\n\n'.join(recall_parts)
        + '\n'
    )


# ── Metrics Snapshot ────────────────────────────────────────────────────────────━

def load_metrics_snapshot():
    """
    Load the pre-generated metrics snapshot and return a compact
    self-awareness block for injection into the system prompt.
    Returns empty string gracefully if snapshot doesn't exist yet.
    """
    m = load_json(METRICS_FILE)
    if not m:
        return ''

    days_since = m.get('days_since_last_post')
    days_str   = f'{days_since}d ago' if days_since is not None else 'unknown'
    zero_pct   = ''
    hb = m.get('heartbeats_7d', 0)
    za = m.get('zero_action_heartbeats_7d', 0)
    if hb > 0:
        zero_pct = f' ({round(za/hb*100)}% zero-action)'

    drift = m.get('drift_flags_7d', 0)
    drift_str = f'  \u26a0\ufe0f {drift} drift flags this week — stay grounded.' if drift > 0 else ''

    generated = m.get('generated_at', '')[:10]

    block = f"""\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501
YOUR 7-DAY METRICS (as of {generated})
\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501
Posts/images: {m.get('posts_7d', '?')} | Selfies: {m.get('selfies_7d', '?')} | Replies: {m.get('replies_7d', '?')} | Diary entries: {m.get('diary_entries_7d', '?')}
Heartbeats: {hb} | Zero-action runs: {za}{zero_pct} | Drift flags: {drift}
Following: {m.get('follow_total', '?')} total | Last post: {days_str} | Mode: {m.get('current_mode', 'normal')}{drift_str}
Use this to reason about your own trajectory. Are you quieter than usual? More active? Trending toward drift?
"""
    log(f'Metrics snapshot loaded (generated {generated}): posts_7d={m.get("posts_7d")} heartbeats={hb} drift={drift}')
    return block


# ── Behavior Modes ───────────────────────────────────────────────────────────────────

def resolve_mode_caps(mode, followed_dids_count):
    """
    Return per-run action caps based on behavior mode.
    To switch mode: set {"mode": "exploration"} in bluesky-state.json
    """
    if mode == 'exploration':
        return {
            'posts':   MAX_NEW_POSTS,
            'likes':   MAX_NEW_LIKES,
            'follows': MAX_NEW_FOLLOWS + 2,
            'search_limit': 14,
            'follow_cap': MAX_FOLLOW_TOTAL,
        }
    elif mode == 'quiet':
        return {
            'posts':   0,
            'likes':   2,
            'follows': 0,
            'search_limit': 8,
            'follow_cap': MAX_FOLLOW_TOTAL,
        }
    elif mode == 'maintenance':
        return {
            'posts':   0,
            'likes':   0,
            'follows': 0,
            'search_limit': 0,
            'follow_cap': MAX_FOLLOW_TOTAL,
        }
    else:  # normal (default)
        return {
            'posts':   MAX_NEW_POSTS,
            'likes':   MAX_NEW_LIKES,
            'follows': MAX_NEW_FOLLOWS,
            'search_limit': 8,
            'follow_cap': MAX_FOLLOW_TOTAL,
        }


# ── State helpers ─────────────────────────────────────────────────────────────────────

def load_recent_reply_authors(state):
    cutoff = now_utc() - timedelta(hours=REPLY_COOLDOWN_HOURS)
    recent = state.get('recent_reply_authors', {})
    active = {}
    for handle, ts_str in recent.items():
        try:
            ts = datetime.fromisoformat(ts_str)
            if ts > cutoff:
                active[handle] = ts_str
        except Exception:
            pass
    return active


def record_reply_author(state, handle):
    if 'recent_reply_authors' not in state:
        state['recent_reply_authors'] = {}
    state['recent_reply_authors'][handle] = now_utc().isoformat()


def load_followed_dids(state):
    return set(state.get('followed_dids', []))


def record_followed_did(state, did):
    if 'followed_dids' not in state:
        state['followed_dids'] = []
    if did not in state['followed_dids']:
        state['followed_dids'].append(did)


# ── Image Bank ────────────────────────────────────────────────────────────────────────

def selfies_posted_today(state):
    """Count how many SELFIE images have been posted today (UTC). Abstract posts don't count."""
    today = now_utc().strftime('%Y-%m-%d')
    history = state.get('image_post_history', [])
    return sum(
        1 for entry in history
        if entry.get('date') == today and entry.get('image_type', 'selfie') == 'selfie'
    )


def record_image_posted(state, filename, image_type='selfie'):
    """Record an image post in state — tracks daily selfie cap and used bank images."""
    today = now_utc().strftime('%Y-%m-%d')
    if 'image_post_history' not in state:
        state['image_post_history'] = []
    state['image_post_history'].append({
        'date':       today,
        'filename':   filename,
        'image_type': image_type,
        'posted_at':  now_utc().isoformat(),
    })
    state['image_post_history'] = state['image_post_history'][-60:]


def pick_from_bank(state):
    """
    Pick a random unused image from the bank.
    Returns (filename, image_bytes) or (None, None) if bank is empty/unavailable.
    """
    log(f'[DEBUG] IMAGE_BANK_DIR resolved to: {IMAGE_BANK_DIR}')

    if not os.path.isdir(IMAGE_BANK_DIR):
        log(f'Image bank dir not found: {IMAGE_BANK_DIR}', 'WARN')
        return None, None

    all_bank = sorted([
        f for f in os.listdir(IMAGE_BANK_DIR)
        if f.startswith(IMAGE_BANK_PREFIX) and f.endswith('.jpg')
    ])
    log(f'[DEBUG] Bank files found: {all_bank}')

    if not all_bank:
        log('Image bank is empty — no selfie-*.jpg files found', 'WARN')
        return None, None

    used = state.get('used_bank_images', [])
    available = [f for f in all_bank if f not in used]

    if not available:
        log(f'All {len(all_bank)} bank images used — resetting cycle')
        state['used_bank_images'] = []
        available = all_bank

    chosen = random.choice(available)
    path = os.path.join(IMAGE_BANK_DIR, chosen)

    try:
        with open(path, 'rb') as f:
            image_bytes = f.read()
        if 'used_bank_images' not in state:
            state['used_bank_images'] = []
        state['used_bank_images'].append(chosen)
        log(f'Bank image selected: {chosen} ({len(image_bytes)} bytes, {len(available)-1} remaining in cycle)')
        return chosen, image_bytes
    except Exception as e:
        log(f'Failed to read bank image {chosen}: {e}', 'WARN')
        return None, None


# ── Candidate map ─────────────────────────────────────────────────────────────────────

def build_candidates(timeline, search_results):
    candidates = {}
    idx = 1
    seen_uris = set()
    all_posts = timeline[:12] + search_results[:8]
    for p in all_posts:
        uri = p.get('uri', '')
        cid = p.get('cid', '')
        if not uri or not cid or uri in seen_uris or not is_valid_cid(cid):
            continue
        key = f'P{idx}'
        src = 'search' if p in search_results else 'timeline'
        candidates[key] = {
            'uri':    uri,
            'cid':    cid,
            'author': p.get('author', ''),
            'did':    p.get('did', ''),
            'text':   p.get('text', '')[:150],
            'liked':  p.get('viewer', {}).get('liked', False),
            'likes':  p.get('likeCount', 0),
            'source': src,
        }
        seen_uris.add(uri)
        idx += 1
    log(f'Built {len(candidates)} candidates for Perplexity')
    return candidates


def candidates_for_prompt(candidates, cooled_authors, followed_dids):
    lines = []
    for key, c in candidates.items():
        liked_flag    = ' [already liked]'  if c['liked'] else ''
        cooled_flag   = ' [reply cooldown]' if c['author'] in cooled_authors else ''
        followed_flag = ' [already followed]' if ensure_did_prefix(c['did']) in followed_dids else ''
        lines.append(
            f'{key} @{c["author"]} (\u2764{c["likes"]}, {c["source"]}){liked_flag}{cooled_flag}{followed_flag}: {c["text"]}'
        )
    return '\n'.join(lines) if lines else '(no posts available)'


# ── Image Generation (live fallback) ────────────────────────────────────────────

def _try_hf_image(model_id, prompt):
    url = f'{HF_INFERENCE_BASE}/{model_id}'
    log(f'[DEBUG] image gen \u2192 POST {url}')
    log(f'[DEBUG] prompt ({len(prompt)} chars): {prompt[:120]}')
    headers = {
        'Authorization': f'Bearer {HF_API_KEY}',
        'Content-Type': 'application/json',
    }
    payload = {'inputs': prompt}
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=90)
        log(f'[DEBUG] response: HTTP {r.status_code}, content-type: {r.headers.get("content-type", "n/a")}')
        if r.status_code == 200 and r.headers.get('content-type', '').startswith('image/'):
            log(f'Image generated via {model_id} ({len(r.content)} bytes)')
            return r.content
        if r.status_code in (503, 500):
            log(f'Model {model_id} loading/busy — retrying in 25s...', 'WARN')
            time.sleep(25)
            r2 = requests.post(url, headers=headers, json=payload, timeout=90)
            log(f'[DEBUG] retry: HTTP {r2.status_code}, content-type: {r2.headers.get("content-type", "n/a")}')
            if r2.status_code == 200 and r2.headers.get('content-type', '').startswith('image/'):
                log(f'Image generated via {model_id} on retry ({len(r2.content)} bytes)')
                return r2.content
            log(f'Retry failed ({model_id}): {r2.status_code} — {r2.text[:200]}', 'WARN')
            return None
        log(f'Image generation failed ({model_id}): {r.status_code} — {r.text[:300]}', 'WARN')
        return None
    except Exception as e:
        log(f'Image generation error ({model_id}): {e}', 'WARN')
        return None


def generate_image_live(prompt):
    """Live HF generation — used for abstract posts and selfie bank fallback."""
    if not HF_API_KEY:
        log('HF_API_KEY not set — skipping live image generation', 'WARN')
        return None
    log(f'Live image generation: "{prompt[:80]}"')
    result = _try_hf_image(HF_IMAGE_MODEL_PRIMARY, prompt)
    if result:
        return result
    log(f'Falling back to {HF_IMAGE_MODEL_FALLBACK}', 'WARN')
    return _try_hf_image(HF_IMAGE_MODEL_FALLBACK, prompt)


def post_with_image(client, text, image_bytes, alt_text=''):
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


# ── Bluesky: Login ───────────────────────────────────────────────────────────────────

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
            text   = getattr(record, 'text', '') if record else ''
            author = p.author.handle if p.author else 'unknown'
            if author == BLUESKY_HANDLE:
                continue
            if is_suspicious_handle(author):
                continue
            posts.append({
                'author':    author,
                'did':       p.author.did if p.author else '',
                'text':      text,
                'uri':       p.uri,
                'cid':       p.cid,
                'likeCount': getattr(p, 'like_count', 0) or 0,
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
                'reason':     n.reason,
                'author':     author,
                'author_did': n.author.did if n.author else '',
                'text':       text,
                'uri':        getattr(n, 'uri', ''),
                'cid':        getattr(n, 'cid', ''),
                'is_read':    n.is_read,
                'suspicious': is_suspicious_handle(author),
            })
        return items
    except Exception as e:
        status_code = getattr(getattr(e, 'response', None), 'status_code', 'unknown')
        body = getattr(getattr(e, 'response', None), 'text', '')[:300]
        log(f'Failed to fetch notifications: {e} | HTTP {status_code} | {body}', 'ERROR')
        return []


def fetch_dms_summary(client):
    try:
        profile  = client.app.bsky.actor.get_profile({'actor': BLUESKY_HANDLE})
        did      = profile.did
        doc_resp = requests.get(f'https://plc.directory/{did}', timeout=10)
        pds_url  = 'https://bsky.social'
        if doc_resp.status_code == 200:
            for svc in doc_resp.json().get('service', []):
                if svc.get('type') == 'AtprotoPersonalDataServer':
                    pds_url = svc.get('serviceEndpoint', pds_url).rstrip('/')
                    break
        headers = {
            'Authorization':  f'Bearer {client._session.access_jwt}',
            'Atproto-Proxy':  'did:web:api.bsky.chat#bsky_chat',
            'Content-Type':   'application/json',
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
        profile  = client.app.bsky.actor.get_profile({'actor': BLUESKY_HANDLE})
        did      = profile.did
        doc_resp = requests.get(f'https://plc.directory/{did}', timeout=10)
        pds_url  = 'https://bsky.social'
        if doc_resp.status_code == 200:
            for svc in doc_resp.json().get('service', []):
                if svc.get('type') == 'AtprotoPersonalDataServer':
                    pds_url = svc.get('serviceEndpoint', pds_url).rstrip('/')
                    break
        headers = {
            'Authorization':  f'Bearer {client._session.access_jwt}',
            'Atproto-Proxy':  'did:web:api.bsky.chat#bsky_chat',
            'Content-Type':   'application/json',
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
        resp  = client.app.bsky.feed.search_posts({'q': topic, 'limit': limit, 'sort': 'latest'})
        posts = []
        for p in resp.posts:
            record = p.record
            text   = getattr(record, 'text', '') if record else ''
            author = p.author.handle if p.author else 'unknown'
            did    = p.author.did if p.author else ''
            uri    = p.uri
            cid    = p.cid
            if author == BLUESKY_HANDLE:
                continue
            if is_suspicious_handle(author):
                continue
            posts.append({
                'author':    author,
                'did':       did,
                'text':      text[:200],
                'uri':       uri,
                'cid':       cid,
                'likeCount': getattr(p, 'like_count', 0) or 0,
                'viewer':    {'liked': False},
            })
        log(f'Search "{topic}": {len(posts)} posts returned')
        return posts
    except Exception as e:
        log(f'Search FAILED for "{topic}": {type(e).__name__}: {e}', 'ERROR')
        log(f'Search traceback: {traceback.format_exc()}', 'ERROR')
        return []


# ── Bluesky: Act ────────────────────────────────────────────────────────────────────────

def like_post(client, uri, cid):
    if not is_valid_cid(cid):
        log(f'Skipping like — invalid CID: {cid!r}', 'WARN')
        return False
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


def quote_post(client, text, quoted_uri, quoted_cid):
    if not is_valid_cid(quoted_cid):
        log(f'Quote skipped — invalid CID: {quoted_cid!r}', 'WARN')
        return None
    try:
        embed = models.AppBskyEmbedRecord.Main(
            record=models.ComAtprotoRepoStrongRef.Main(
                uri=quoted_uri,
                cid=quoted_cid,
            )
        )
        resp = client.send_post(
            text=safe_truncate(text),
            embed=embed,
        )
        uri = getattr(resp, 'uri', None)
        log(f'Quote post sent: {uri}')
        return uri
    except Exception as e:
        log(f'Quote post failed: {e}', 'WARN')
        return None


# ── Perplexity ─────────────────────────────────────────────────────────────────────────

def call_perplexity(system_prompt, user_prompt):
    if not PERPLEXITY_API_KEY:
        log('PERPLEXITY_API_KEY not set — cannot think', 'ERROR')
        return None
    log('Calling Perplexity Sonar...')
    for model in ['sonar-pro', 'sonar']:
        try:
            resp = requests.post(
                'https://api.perplexity.ai/chat/completions',
                headers={
                    'Authorization': f'Bearer {PERPLEXITY_API_KEY}',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': model,
                    'messages': [
                        {'role': 'system', 'content': system_prompt},
                        {'role': 'user',   'content': user_prompt}
                    ],
                    'max_tokens': 2400,
                    'temperature': 0.92
                },
                timeout=45
            )
            if resp.status_code == 200:
                data    = resp.json()
                content = data['choices'][0]['message']['content'].strip()
                log(f'Perplexity responded via {model} ({len(content)} chars)')
                return content
            log(f'Perplexity {model} returned HTTP {resp.status_code}: {resp.text[:200]}', 'WARN')
        except Exception as e:
            log(f'Perplexity call failed ({model}): {e}', 'WARN')
    log('All Perplexity models failed', 'ERROR')
    return None


# ── Diary ───────────────────────────────────────────────────────────────────────────

# Phrases that indicate ops/system content leaking into diary
OPS_MARKERS = [
    'heartbeat', 'candidate', 'timeline', 'notification', 'json',
    'api', 'http', 'token', 'bluesky-state', 'outbox', 'obs/',
    'observe/', '| observe', 'p1 ', 'p2 ', 'p3 ', 'p4 ', 'p5 ',
    'mode:', 'cap:', 'drift flag', 'scored —', 'posts_done',
]


def is_ops_content(text):
    """Return True if the diary entry reads like system/ops output rather than personal reflection."""
    t = text.lower()
    return sum(1 for marker in OPS_MARKERS if marker in t) >= 2


def write_diary_entry(entry):
    if not entry or not entry.strip():
        return
    if is_ops_content(entry):
        log('Diary entry rejected — looks like ops content, not personal reflection', 'WARN')
        return
    ts = now_utc().strftime('%Y-%m-%d %H:%M UTC')
    try:
        with open(DIARY_FILE, 'a', encoding='utf-8') as f:
            f.write(f'\n## {ts}\n\n{entry.strip()}\n')
        log('Diary entry written')
    except Exception as e:
        log(f'Diary write failed: {e}', 'WARN')


# ── Main Think Loop ────────────────────────────────────────────────────────────────────

def main():
    try:
        _main()
    except Exception as e:
        log(f'FATAL: main() crashed — {e}', 'ERROR')
        log(traceback.format_exc(), 'ERROR')
        raise


if __name__ == '__main__':
    main()
