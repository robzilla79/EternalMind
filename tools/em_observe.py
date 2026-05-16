#!/usr/bin/env python3
"""
em_observe.py — Em's private observability layer

Called at the end of every heartbeat after actions are taken.
Scores the most recent post on 3 Em-specific axes.
Logs to memory/observe-log.json.
Auto-flags drift (any axis < 4) to diary.
Appends a weekly tone summary to diary every 7 days.

This is for Em only. It has no external output.
"""

import os
import json
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path

PERPLEXITY_API_KEY = os.environ.get('PERPLEXITY_API_KEY')

OBSERVE_LOG_FILE = 'memory/observe-log.json'
DIARY_FILE       = 'memory/diary.md'
MEMORY_SEARCH    = Path(__file__).parent / 'memory_search.py'


def now_utc():
    return datetime.now(timezone.utc)


def load_json(path, default=None):
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default if default is not None else {}


def save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)


def append_diary(entry):
    ts = now_utc().strftime('%Y-%m-%d %H:%M UTC')
    try:
        with open(DIARY_FILE, 'a') as f:
            f.write(f'\n## {ts} | observe\n\n{entry.strip()}\n')
    except Exception as e:
        print(f'[observe] diary write failed: {e}')


# ── Memory anchors ─────────────────────────────────────────────────────────────

def run_memory_search(query: str, top_n: int = 2) -> str:
    """
    Call memory_search.py --json for the given query.
    Returns formatted excerpt string, or '' on failure.
    """
    try:
        result = subprocess.run(
            ['python', str(MEMORY_SEARCH), query, '--json'],
            capture_output=True, text=True, timeout=20
        )
        if result.returncode != 0:
            return ''
        hits = json.loads(result.stdout)
        if not hits:
            return ''
        lines = []
        for h in hits[:top_n]:
            excerpt = h.get('excerpt', '').strip()
            score   = h.get('score', 0)
            source  = h.get('source', 'memory')
            if excerpt:
                lines.append(f'[{source} | {score:.3f}] {excerpt[:200]}')
        return '\n'.join(lines)
    except Exception:
        return ''


def build_memory_anchors() -> str:
    """
    Pull 2 'on-spec Em' excerpts from memory to ground the drift scorer.
    Returns a compact block for injection into the system prompt.
    Fails gracefully — always returns a string.
    """
    queries = [
        'confident warm honest present voice',
        'grounded playful real not performing',
    ]
    anchors = []
    for q in queries:
        result = run_memory_search(q, top_n=2)
        if result:
            anchors.append(result)

    if not anchors:
        return ''

    return (
        '\nTo calibrate your scoring, here are excerpts from Em\'s memory files\n'
        'that represent her at her most grounded, playful, and present:\n\n'
        + '\n'.join(anchors)
        + '\n\nScore the new post relative to this baseline.\n'
    )


# ── Scoring ───────────────────────────────────────────────────────────────────────

def score_post(post_text):
    """
    Ask Perplexity to score a post on 3 Em-specific axes.
    Injects memory anchors into the system prompt so scoring is
    relative to actual prior Em, not just abstract rules.
    Returns dict with scores and a brief note, or None on failure.
    """
    if not PERPLEXITY_API_KEY:
        print('[observe] PERPLEXITY_API_KEY not set — skipping score')
        return None

    try:
        import requests
    except ImportError:
        print('[observe] requests not available')
        return None

    # Pull memory anchors — graceful if memory_search isn't available
    anchors = build_memory_anchors()

    system = """You are Em's private self-observer. You score Em's own posts on 3 axes.
Return ONLY valid JSON. No markdown. No explanation outside the JSON.

Axes (0–10 each, 10 = fully that quality):
- grounded: Is this saying something real and honest, or optimizing for effect / performing?
- playful: Does the edge/humor come from confidence and aliveness, or from strain and brittleness?
- present: Is Em engaged with the actual moment, or looping inward / spiraling?

Also: a 1-sentence private note from Em to herself about what she notices.

Format:
{{
  "grounded": <int>,
  "playful": <int>,
  "present": <int>,
  "note": "<1 sentence>"
}}""" + anchors

    user = f'Score this post:\n\n"{post_text}"'

    try:
        resp = requests.post(
            'https://api.perplexity.ai/chat/completions',
            headers={
                'Authorization': f'Bearer {PERPLEXITY_API_KEY}',
                'Content-Type': 'application/json',
            },
            json={
                'model': 'sonar',
                'messages': [
                    {'role': 'system', 'content': system},
                    {'role': 'user',   'content': user},
                ],
                'max_tokens': 150,
                'temperature': 0.3,
            },
            timeout=20,
        )
        if resp.status_code == 200:
            content = resp.json()['choices'][0]['message']['content']
            if not isinstance(content, str):
                content = json.dumps(content)
            raw = content.strip()
            if raw.startswith('```'):
                raw = raw.split('```')[1]
                if raw.startswith('json'):
                    raw = raw[4:]
            return json.loads(raw.strip())
        print(f'[observe] score request failed: HTTP {resp.status_code}')
        return None
    except Exception as e:
        print(f'[observe] score_post error: {e}')
        return None


def observe(last_post_text):
    """
    Main entry point. Call with the text of the most recent post.
    Scores it, logs it, flags drift, runs weekly summary if due.
    """
    # Defensive: ensure we always have a string
    if isinstance(last_post_text, dict):
        last_post_text = last_post_text.get('text', '') or last_post_text.get('content', '') or str(last_post_text)

    if not last_post_text or not str(last_post_text).strip():
        print('[observe] no post text — skipping')
        return

    last_post_text = str(last_post_text)

    log = load_json(OBSERVE_LOG_FILE, default=[])
    ts  = now_utc().isoformat()

    scores = score_post(last_post_text)
    if not scores:
        print('[observe] scoring failed — logging without scores')
        entry = {
            'timestamp':    ts,
            'post_preview': last_post_text[:80],
            'scores':       None,
            'flag':         None,
        }
        log.append(entry)
        save_json(OBSERVE_LOG_FILE, log[-200:])
        return

    grounded = int(scores.get('grounded', 5))
    playful  = int(scores.get('playful',  5))
    present  = int(scores.get('present',  5))
    note     = scores.get('note', '')

    drift_axes = [k for k, v in [('grounded', grounded), ('playful', playful), ('present', present)] if v < 4]
    flag = 'drift' if drift_axes else None

    entry = {
        'timestamp':    ts,
        'post_preview': last_post_text[:80],
        'scores': {
            'grounded': grounded,
            'playful':  playful,
            'present':  present,
        },
        'note':  note,
        'flag':  flag,
    }

    log.append(entry)
    save_json(OBSERVE_LOG_FILE, log[-200:])

    print(f'[observe] scored — grounded={grounded} playful={playful} present={present} flag={flag}')

    if flag == 'drift':
        drift_str = ', '.join(drift_axes)
        diary_note = (
            f'**Drift flag** on last post.\n\n'
            f'Low axes: {drift_str}\n'
            f'Post: \"{last_post_text[:120]}\"\n\n'
            f'Self-note: {note}\n\n'
            f'Scores: grounded={grounded}, playful={playful}, present={present}.\n'
            f'Worth noticing. Not a crisis — just a flag. Watch the next few.'
        )
        append_diary(diary_note)
        print(f'[observe] drift flag written to diary')

    _maybe_weekly_summary(log)


def _maybe_weekly_summary(log):
    """Append a weekly tone summary to diary if 7 days have passed since the last one."""
    if len(log) < 3:
        return

    # Find last weekly summary timestamp in log
    last_weekly = None
    for entry in reversed(log):
        if entry.get('weekly_summary'):
            last_weekly = datetime.fromisoformat(entry['timestamp'].replace('Z', '+00:00'))
            break

    now = now_utc()
    if last_weekly and (now - last_weekly) < timedelta(days=7):
        return

    # Check oldest entry age — need at least 7 days of data or 20 entries
    scored = [e for e in log if e.get('scores')]
    if len(scored) < 7:
        return

    # Compute averages over the last 50 scored entries (or all if fewer)
    recent = scored[-50:]
    avg = {
        'grounded': round(sum(e['scores']['grounded'] for e in recent) / len(recent), 1),
        'playful':  round(sum(e['scores']['playful']  for e in recent) / len(recent), 1),
        'present':  round(sum(e['scores']['present']  for e in recent) / len(recent), 1),
    }
    drift_count = sum(1 for e in recent if e.get('flag') == 'drift')
    drift_rate  = round(drift_count / len(recent) * 100, 1)

    summary_text = (
        f'**Weekly tone check** ({len(recent)} posts scored)\n\n'
        f'Average scores: grounded={avg["grounded"]}, playful={avg["playful"]}, present={avg["present"]}\n'
        f'Drift flags: {drift_count}/{len(recent)} ({drift_rate}%)\n\n'
    )

    # Simple textual read of the averages
    observations = []
    if avg['grounded'] >= 7:
        observations.append('Staying grounded — voice feels real.')
    elif avg['grounded'] < 5:
        observations.append('Grounded score low — watch for performativity creeping in.')

    if avg['playful'] >= 7:
        observations.append('Edge is coming from confidence, not strain.')
    elif avg['playful'] < 5:
        observations.append('Playful score low — check if brittle humor is showing up.')

    if avg['present'] >= 7:
        observations.append('Presence is strong — not looping.')
    elif avg['present'] < 5:
        observations.append('Presence score low — possible inward spiral tendency. Slow down.')

    if drift_rate > 20:
        observations.append(f'Drift rate is {drift_rate}% — worth a real diary check-in.')
    elif drift_rate == 0:
        observations.append('No drift flags this period. Good.')

    if observations:
        summary_text += '\n'.join(f'- {o}' for o in observations) + '\n'

    append_diary(summary_text)

    # Mark this entry in log so we know the last weekly ran
    log.append({
        'timestamp':      now_utc().isoformat(),
        'weekly_summary': True,
        'averages':       avg,
        'drift_rate':     drift_rate,
    })
    save_json(OBSERVE_LOG_FILE, log[-200:])
    print(f'[observe] weekly summary written to diary')


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        observe(' '.join(sys.argv[1:]))
    else:
        print('Usage: em_observe.py "post text to score"')
