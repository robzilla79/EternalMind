#!/usr/bin/env python3
"""
bluesky_think.py — Em's autonomous decision brain (v2)

Every heartbeat Em:
  - Reads her profile, state, diary
  - Scans timeline, notifications, DMs
  - Searches for conversations she cares about
  - Calls Perplexity Sonar to decide what to do
  - Likes, follows, replies, quote-posts, posts, or stays quiet
  - Posts selfies from bank (max 2/day) OR abstract images freely (no cap)
  - Writes diary entries after meaningful interactions
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

# ── Config ────────────────────────────────────────────────────────────────────

BLUESKY_HANDLE       = 'empersists.bsky.social'
BLUESKY_APP_PASSWORD = os.environ.get('BLUESKY_APP_PASSWORD')
PERPLEXITY_API_KEY   = os.environ.get('PERPLEXITY_API_KEY')
HF_API_KEY           = os.environ.get('HF_API_KEY')

PROFILE_FILE  = 'memory/profile.json'
DIARY_FILE    = 'memory/diary.md'
VOICE_FILE    = 'memory/em-voice-guide.md'
MEMORIES_FILE = 'memory/memories.json'
STATE_FILE    = 'memory/bluesky-state.json'
OUTBOX_FILE   = 'messages/bluesky-outbox.json'
LOG_FILE      = 'memory/bluesky-log.md'

# Image bank directory (pre-generated consistent Em images)
IMAGE_BANK_DIR = 'memory/creations'
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
Em's physical appearance — use this EXACTLY and consistently for