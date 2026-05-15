#!/usr/bin/env python3
"""
em_heartbeat_close.py — Called at the end of every _main() heartbeat.

Handles:
  1. Writing metrics to memory/em-metrics.json
  2. Flushing any self-authored memories from decision to memory/em-memory-queue.json
  3. Logging mode + metrics summary to the run log

Designed to be a small, stable file that never needs to grow.
This exists because bluesky_think.py is too large to safely patch via API.
"""

import json
import os
from datetime import datetime, timezone, timedelta

REPO_ROOT         = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
METRICS_FILE      = os.path.join(REPO_ROOT, 'memory/em-metrics.json')
MEMORY_QUEUE_FILE = os.path.join(REPO_ROOT, 'memory/em-memory-queue.json')
LOG_FILE          = os.path.join(REPO_ROOT, 'memory/bluesky-log.md')


def _log(msg):
    ts = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
    print(f'[INFO] [close] {msg}')
    try:
        with open(LOG_FILE, 'a') as f:
            f.write(f'### {ts} — ✓ [close] {msg}\n\n')
    except Exception:
        pass


def _load_json(path, default=None):
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default if default is not None else {}


def _save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)


def flush_metrics(posts=0, replies=0, likes=0, follows=0, images=0,
                  silent=False, guardrail_hits=None):
    """
    Update em-metrics.json with this heartbeat's activity.

    Call at the end of _main() with actual counts:
        flush_metrics(posts=posts_done, replies=replies_done,
                      likes=likes_done, follows=follows_done,
                      images=images_done, silent=(posts_done + likes_done + follows_done == 0))
    """
    if guardrail_hits is None:
        guardrail_hits = {}

    metrics = _load_json(METRICS_FILE, default={})
    today   = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    metrics['last_updated'] = datetime.now(timezone.utc).isoformat()

    # Daily entry
    daily = metrics.setdefault('daily', [])
    today_entry = next((d for d in daily if d.get('date') == today), None)
    if not today_entry:
        today_entry = {
            'date': today, 'posts': 0, 'replies': 0, 'likes': 0,
            'follows': 0, 'heartbeats': 0, 'silent_heartbeats': 0, 'images': 0
        }
        daily.append(today_entry)

    today_entry['posts']            += posts
    today_entry['replies']          += replies
    today_entry['likes']            += likes
    today_entry['follows']          += follows
    today_entry['images']           += images
    today_entry['heartbeats']       += 1
    if silent:
        today_entry['silent_heartbeats'] += 1
    metrics['daily'] = sorted(daily, key=lambda d: d['date'])[-60:]

    # Rolling windows
    cutoff_7  = (datetime.now(timezone.utc) - timedelta(days=7)).strftime('%Y-%m-%d')
    cutoff_30 = (datetime.now(timezone.utc) - timedelta(days=30)).strftime('%Y-%m-%d')
    for wkey, cutoff in [('rolling_7d', cutoff_7), ('rolling_30d', cutoff_30)]:
        w = {k: 0 for k in metrics.get(wkey, {'posts':0,'replies':0,'likes':0,'follows':0,
                                               'heartbeats':0,'silent_heartbeats':0,'images':0})}
        for d in metrics['daily']:
            if d['date'] >= cutoff:
                for k in w:
                    w[k] += d.get(k, 0)
        metrics[wkey] = w

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

    _save_json(METRICS_FILE, metrics)
    _log(f'Metrics updated — posts:{posts} replies:{replies} likes:{likes} follows:{follows} images:{images} silent:{silent}')


def flush_memories(new_memories):
    """
    Append self-authored memories to em-memory-queue.json.

    new_memories: list of dicts with keys: summary, tags (optional), source (optional)
    Example:
        flush_memories([{'summary': 'Had a good reply thread about continuity of self with @someone',
                         'tags': ['social', 'philosophy']}])
    """
    if not new_memories:
        return
    queue = _load_json(MEMORY_QUEUE_FILE, default={'pending': []})
    queue.setdefault('pending', [])
    for m in new_memories:
        queue['pending'].append({
            'summary':   m.get('summary', ''),
            'tags':      m.get('tags', []),
            'source':    m.get('source', 'heartbeat'),
            'queued_at': datetime.now(timezone.utc).isoformat(),
        })
    _save_json(MEMORY_QUEUE_FILE, queue)
    _log(f'{len(new_memories)} memory/memories queued for promotion')


def heartbeat_close(posts_done=0, replies_done=0, likes_done=0, follows_done=0,
                    images_done=0, guardrail_hits=None, new_memories=None):
    """
    Single call to close out a heartbeat cleanly.
    Add this at the end of _main() in bluesky_think.py:

        from em_heartbeat_close import heartbeat_close
        heartbeat_close(
            posts_done=posts_done,
            replies_done=replies_done,
            likes_done=likes_done,
            follows_done=follows_done,
            images_done=images_done,
            guardrail_hits=guardrail_hits,
            new_memories=new_memories,
        )
    """
    silent = (posts_done + replies_done + likes_done + follows_done + images_done) == 0
    flush_metrics(
        posts=posts_done,
        replies=replies_done,
        likes=likes_done,
        follows=follows_done,
        images=images_done,
        silent=silent,
        guardrail_hits=guardrail_hits or {},
    )
    flush_memories(new_memories or [])
