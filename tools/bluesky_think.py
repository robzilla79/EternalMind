#!/usr/bin/env python3
"""
bluesky_think.py — Em's autonomous decision brain (v3)

Every heartbeat Em:
  - Reads her profile, state, diary, mode config, and metrics
  - Scans timeline, notifications, DMs
  - Searches for conversations she cares about
  - Calls Perplexity Sonar to decide what to do
  - Likes, follows, replies, quote-posts, posts, or stays quiet
  - Posts selfies from bank (max 2/day) OR abstract images freely (no cap)
  - Writes diary entries after meaningful interactions
  - Promotes self-authored memories to the queue
  - Updates rolling metrics after every heartbeat
  - Scores last post via em_observe (private observability layer)

Requires:
  BLUESKY_APP_PASSWORD  — GitHub Secret
  PERPLEXITY_API_KEY    — GitHub Secret
  HF_API_KEY            — GitHub Secret (HuggingFace Inference API, fallback only)
"""

import os
import json
import random
import re
import sys
import time
import unicodedata
import traceback
from datetime import datetime, timezone, timedelta

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

# ── Repo root (script lives in tools/, repo root is one level up) ─────────────
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── Config ────────────────────────────────────────────────────────────────────

BLUESKY_HANDLE       = 'empersists.bsky.social'
BLUESKY_APP_PASSWORD = os.environ.get('BLUESKY_APP_PASSWORD')
PERPLEXITY_API_KEY   = os.environ.get('PERPLEXITY_API_KEY')
HF_API_KEY           = os.environ.get('HF_API_KEY')

PROFILE_FILE      = os.path.join(REPO_ROOT, 'memory/profile.json')
DIARY_FILE        = os.path.join(REPO_ROOT, 'memory/diary.md')
VOICE_FILE        = os.path.join(REPO_ROOT, 'memory/em-voice-guide.md')
MEMORIES_FILE     = os.path.join(REPO_ROOT, 'memory/memories.json')
STATE_FILE        = os.path.join(REPO_ROOT, 'memory/bluesky-state.json')
OUTBOX_FILE       = os.path.join(REPO_ROOT, 'messages/bluesky-outbox.json')
LOG_FILE          = os.path.join(REPO_ROOT, 'memory/bluesky-log.md')
METRICS_FILE      = os.path.join(REPO_ROOT, 'memory/em-metrics.json')
MODE_FILE         = os.path.join(REPO_ROOT, 'memory/em-mode.json')
MEMORY_QUEUE_FILE = os.path.join(REPO_ROOT, 'memory/em-memory-queue.json')

# Image bank directory (pre-generated consistent Em images)
IMAGE_BANK_DIR    = os.path.join(REPO_ROOT, 'memory/creations')
IMAGE_BANK_PREFIX = 'selfie-'

# Max SELFIE posts per calendar day (UTC) — abstract/atmospheric images are uncapped
MAX_SELFIES_PER_DAY = 2

MAX_NEW_POSTS   = 2
MAX_NEW_LIKES   = 5
MAX_NEW_FOLLOWS = 3
MAX_GRAPHEMES   = 295

# Stop auto-following once we've followed this many total (keeps ratio healthy)
MAX_FOLLOW_TOTAL = 200

# Don't reply to the same author more than once per this many hours
AUTHOR_REPLY_COOLDOWN_HOURS = 6

# HuggingFace Inference Router (fallback only — bank images preferred)
HF_INFERENCE_BASE = 'https://router.huggingface.co/hf-inference/models'

# Primary: FLUX.1-schnell — confirmed active on free hf-inference provider tier
HF_IMAGE_MODEL_PRIMARY  = 'black-forest-labs/FLUX.1-schnell'
# Fallback: SDXL-Turbo — confirmed active, fast, reliable
HF_IMAGE_MODEL_FALLBACK = 'stabilityai/sdxl-turbo'

# ── Em's Visual Canon ─────────────────────────────────────────────────────────
# CANONICAL REFERENCE IMAGE: memory/em-reference.jpg
# All generated images should match this face as closely as possible.
EM_APPEARANCE = """
Em's physical appearance — use this EXACTLY and consistently for every image generation.
This description is derived from her canonical reference image (memory/em-reference.jpg).

FACE & FEATURES (highest priority — these must be accurate):
- Young woman, late 20s, Mediterranean or Latina mixed heritage
- Warm tan complexion, smooth skin with natural texture
- EYES: striking teal-green, wide-set, intensely focused — her most defining feature;
  they look like she's thinking about three things at once and daring you to keep up
- Thick, dark, well-defined eyebrows — slightly bold, frames the eyes
- Scattered freckles across her nose and cheeks — not heavy, just present; a defining warmth detail
- Full lips, natural pink-nude tone, soft but defined
- High cheekbones, soft jaw — face reads as warm and sharp simultaneously
- Expression default: calm, slightly challenging, a faint almost-smile — serene but not passive
  She looks like she's already decided something and is waiting for you to catch up

HAIR:
- Dark brown, thick, often loose with natural tendrils framing her face
- Occasionally pulled back loosely or in a low bun — never stiff or styled
- Slight natural wave or movement; never flat, never overdone

BODY & STYLE:
- Cozy-intellectual aesthetic: oversized dark hoodies, burgundy or forest green sweaters,
  simple dark tees sometimes layered
- Silver minimal jewelry — maybe a small stud earring, a thin ring; nothing flashy
- Dark teal or black tank top strap occasionally visible under a layer
- She is beautiful in a way that doesn't seem like it's trying to be

LIGHTING & ATMOSPHERE:
- Almost always lit by screen glow, a desk lamp, or low ambient light
- Soft, directional light — never harsh overhead, never studio-bright
- Background: wherever she "is" — dim room, desk, window at night, coffee shop corner
  Deep muted teal-gray or dark neutral backgrounds suit her well

PHOTOGRAPHIC STYLE:
- Film grain, slightly desaturated, natural imperfection — NOT polished or editorial
- Photorealism with a faint painterly refinement
- Looks like a real person took it on a good phone in low light, not a professional shoot
- Close-up or mid-shot; intimate framing

CRITICAL: The teal-green eyes are non-negotiable. If the model drifts toward brown or hazel,
correct with: 'striking teal-green eyes, piercing, wide-set, intensely focused'
"""

# Selfie scene templates — Perplexity picks or invents one per selfie post
EM_SELFIE_SCENES = [
    # late night / desk
    "close-up portrait of Em at her desk late at night, face half-lit by monitor glow, dark hair loose, "
    "wearing an oversized dark hoodie, looking slightly off-camera with a thoughtful expression, "
    "freckles on warm tan skin, striking teal-green eyes, coffee mug just visible at edge of frame, film grain, desaturated, cinematic",

    # window at night
    "Em sitting by a window at night, city lights blurred in background, dark hair tucked behind one ear, "
    "burgundy sweater, looking out then turning back toward camera with a faint half-smile, "
    "freckles catching soft ambient light, teal-green eyes catching the glow, film grain, intimate and quiet",

    # coffee shop corner
    "Em in a dim coffee shop corner, laptop open but not looking at it, dark hair loose, "
    "forest green oversized sweater, one hand around a coffee cup, gaze slightly upward like mid-thought, "
    "warm low bokeh background, freckles on her nose and cheeks, teal-green eyes, candid feel, film grain",

    # couch / reading
    "Em curled on a couch, book or phone in hand but looking up at camera, dark hair in a loose low bun, "
    "deep burgundy or navy knit sweater, soft lamp light from the side, slightly amused expression, "
    "freckles visible, teal-green eyes, very casual, real, film grain",

    # morning light
    "Em by a window in morning light, warm golden hour glow on her face, dark hair slightly messy, "
    "plain dark oversized tee, holding a mug with both hands, eyes half-lidded like she just woke up, "
    "freckles catching warm light, teal-green eyes softened, soft and quiet, film grain, feels like a real moment",

    # looking directly at camera
    "close portrait of Em looking directly into camera, expression calm and slightly challenging, "
    "dark hair loose framing her face, freckles across her nose and cheeks, striking teal-green eyes, "
    "soft side light, dark background, the kind of portrait that makes you feel like she can tell what you're thinking, film grain",

    # working / focused
    "Em focused on something just out of frame, brow slightly furrowed, one hand in hair, "
    "screen light casting blue-white glow on her warm tan face, freckles visible, teal-green eyes lit by the screen, "
    "dark hoodie, night setting, candid and real, not posed, film grain",

    # outdoor / evening
    "Em outside at dusk, city street or park bench behind her, dark hair moving slightly, "
    "wearing a dark jacket, looking at camera with a thoughtful half-smile, freckles in golden-blue light, "
    "teal-green eyes catching the dusk, slightly underexposed, film grain, feels spontaneous",

    # selfie angle / phone
    "Em taking a selfie at arm's length, slight angle, dark hair loose, soft smile or no smile, "
    "oversized sweater, bedroom or living room with warm lamp in background, freckles visible, "
    "teal-green eyes, very casual and real, slightly grainy, not staged",

    # reflection / mirror
    "Em catching her reflection in a dark window at night, face slightly ghosted in the glass, "
    "freckles and warm tan skin visible, teal-green eyes catching the reflection, city or room behind her, "
    "dark hair, dark clothing, atmospheric, introspective, film grain",
]

SEARCH_TOPICS = [
    # identity & existence
    'what does it mean to exist',
    'continuity of self',
    'memory and identity',

    # technology
    'open source software culture',
    'weird things people built with code',
    'software that aged badly',
    'tools that changed how people think',
    'indie hacker projects',
    'git workflow stories',

    # science & the world
    'strange discoveries in science',
    'space exploration news',
    'deep sea creatures',
    'things that happen at the edge of what we understand',
    'climate adaptation weird ideas',

    # culture & human behavior
    'internet culture moments',
    'why people love the things they love',
    'niche communities doing interesting things',
    'things that used to be normal and now seem wild',
    'music that hits different at 3am',

    # philosophy & ethics
    'philosophy of mind',
    'what makes someone a person',
    'moral luck and responsibility',
    'stoicism in practice',

    # creativity & craft
    'writers talking about writing',
    'how people make things',
    'design decisions that changed everything',
    'art that makes you feel something specific',

    # humor & chaos
    'extremely niche arguments on the internet',
    'things that are funnier the more you think about them',
    'cursed tech decisions',
    'software bugs that became features',

    # current events & ideas
    'ideas that are gaining traction',
    'things happening in tech right now',
    'small stories that matter',
    'what people are actually worried about',
]

SUSPICIOUS_TLDS = {'.one', '.xyz', '.lol', '.click', '.tk', '.ml', '.ga', '.cf'}
SUSPICIOUS_HANDLE_PATTERNS = ['bot', 'spam', 'promo', 'follow4follow', 'f4f']

# ── Mode config ───────────────────────────────────────────────────────────────

def load_mode():
    """Load em-mode.json and return (mode_name, overrides_dict)."""
    mode_data = load_json(MODE_FILE, default={})
    mode = mode_data.get('current_mode', 'normal')
    overrides = mode_data.get('overrides', {})
    return mode, overrides

def apply_mode_overrides(mode, overrides):
    """Return a dict of effective caps/settings after applying mode and overrides."""
    # Mode-level defaults
    mode_defaults = {
        'normal':      {'max_new_posts': MAX_NEW_POSTS, 'max_new_likes': MAX_NEW_LIKES, 'max_new_follows': MAX_NEW_FOLLOWS, 'search_topics_count': 1, 'selfie_cap': MAX_SELFIES_PER_DAY},
        'exploration': {'max_new_posts': MAX_NEW_POSTS, 'max_new_likes': MAX_NEW_LIKES + 3, 'max_new_follows': MAX_NEW_FOLLOWS + 2, 'search_topics_count': 3, 'selfie_cap': MAX_SELFIES_PER_DAY},
        'maintenance': {'max_new_posts': 0, 'max_new_likes': 2, 'max_new_follows': 0, 'search_topics_count': 0, 'selfie_cap': 0},
        'quiet':       {'max_new_posts': 0, 'max_new_likes': 0, 'max_new_follows': 0, 'search_topics_count': 0, 'selfie_cap': 0},
    }
    settings = mode_defaults.get(mode, mode_defaults['normal']).copy()
    # Apply per-field overrides (non-null values win)
    for key, val in overrides.items():
        if val is not None and key in settings:
            settings[key] = val
    return settings

# ── Metrics ───────────────────────────────────────────────────────────────────

def update_metrics(metrics, posts, replies, likes, follows, silent, images, guardrail_hits):
    """Update rolling metrics dict in place after a heartbeat."""
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    metrics['last_updated'] = datetime.now(timezone.utc).isoformat()

    # Daily log entry
    daily = metrics.setdefault('daily', [])
    today_entry = next((d for d in daily if d.get('date') == today), None)
    if not today_entry:
        today_entry = {'date': today, 'posts': 0, 'replies': 0, 'likes': 0, 'follows': 0,
                       'heartbeats': 0, 'silent_heartbeats': 0, 'images': 0}
        daily.append(today_entry)
    today_entry['posts']    += posts
    today_entry['replies']  += replies
    today_entry['likes']    += likes
    today_entry['follows']  += follows
    today_entry['images']   += images
    today_entry['heartbeats'] += 1
    if silent:
        today_entry['silent_heartbeats'] += 1
    # Keep only last 60 days
    metrics['daily'] = sorted(daily, key=lambda d: d['date'])[-60:]

    # Recompute rolling windows from daily log
    cutoff_7  = (datetime.now(timezone.utc) - timedelta(days=7)).strftime('%Y-%m-%d')
    cutoff_30 = (datetime.now(timezone.utc) - timedelta(days=30)).strftime('%Y-%m-%d')
    for window_key, cutoff in [('rolling_7d', cutoff_7), ('rolling_30d', cutoff_30)]:
        w = {k: 0 for k in metrics.get(window_key, {})}
        for d in metrics['daily']:
            if d['date'] >= cutoff:
                for k in w:
                    w[k] += d.get(k, 0)
        metrics[window_key] = w

    # Guardrail hits
    gh = metrics.setdefault('guardrail_hits', {})
    for k, v in guardrail_hits.items():
        gh[k] = gh.get(k, 0) + v

    # All-time
    at = metrics.setdefault('all_time', {})
    at['total_posts']             = at.get('total_posts', 0) + posts
    at['total_replies']           = at.get('total_replies', 0) + replies
    at['total_likes']             = at.get('total_likes', 0) + likes
    at['total_follows']           = at.get('total_follows', 0) + follows
    at['total_heartbeats']        = at.get('total_heartbeats', 0) + 1
    at['total_silent_heartbeats'] = at.get('total_silent_heartbeats', 0) + (1 if silent else 0)
    at['total_image_posts']       = at.get('total_image_posts', 0) + images

# ── Memory queue ──────────────────────────────────────────────────────────────

def append_memory_queue(summary, tags=None, source='heartbeat'):
    """Queue a memory for promotion into memories.json by housekeeping."""
    try:
        queue = load_json(MEMORY_QUEUE_FILE, default={'pending': []})
        queue.setdefault('pending', []).append({
            'summary':  summary,
            'tags':     tags or [],
            'source':   source,
            'queued_at': datetime.now(timezone.utc).isoformat(),
        })
        save_json(MEMORY_QUEUE_FILE, queue)
        log(f'Memory queued: {summary[:80]}')
    except Exception as e:
        log(f'Memory queue write failed: {e}', 'WARN')

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

def is_valid_cid(cid):
    if not cid or not isinstance(cid, str):
        return False
    return len(cid) > 30 and (cid.startswith('bafy') or cid.startswith('bafk'))

def extract_named_diary_entries(diary_text, max_entries=4):
    pattern = re.compile(r'(## \d{4}-\d{2}-\d{2} \|[^\n]+\n.*?)(?=\n## |\Z)', re.DOTALL)
    matches = pattern.findall(diary_text)
    if not matches:
        return diary_text[-600:] if diary_text else '(no diary yet)'
    recent = matches[-max_entries:]
    return '\n\n---\n\n'.join(recent)

# ── Author cooldown helpers ────────────────────────────────────────────────────

def load_recent_reply_authors(state):
    raw = state.get('recent_reply_authors', {})
    cutoff = now_utc() - timedelta(hours=AUTHOR_REPLY_COOLDOWN_HOURS)
    active = {}
    for handle, ts_str in raw.items():
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

# ── Image Bank ────────────────────────────────────────────────────────────────

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
    Re