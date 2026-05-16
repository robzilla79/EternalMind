#!/usr/bin/env python3
"""
em_think.py — Em's autonomous reasoning and action layer.

Runs on a schedule (every 30 min during active hours).
Loads context from key memory files + recent Bluesky inbox,
asks Perplexity what needs attention, then executes a structured
action list via GitHub API.

Actions supported:
  - diary_entry     : append an entry to memory/diary.md
  - queue_post      : add a post to messages/bluesky-outbox.json
  - reply_bluesky   : queue a reply to a specific Bluesky notification
  - update_status   : update the MOOD/UPDATED markers in public/index.html
  - update_status_md: rewrite memory/status.md with current state summary
  - fix_file        : rewrite a file in the repo (for broken HTML, nav, etc)
  - log             : write a note to memory/autonomous-log.md (always happens)
  - nothing         : no action needed this cycle

All judgment — including who to reply to and how — happens in the LLM call.
This script executes. The reasoning layer decides.
"""

import os
import json
import re
from datetime import datetime, timezone
from pathlib import Path

PERPLEXITY_API_KEY = os.environ.get('PERPLEXITY_API_KEY')
GITHUB_TOKEN       = os.environ.get('GITHUB_TOKEN')
GITHUB_REPO        = os.environ.get('GITHUB_REPOSITORY', 'robzilla79/EternalMind')

DIARY_FILE         = Path('memory/diary.md')
SCHEDULE_FILE      = Path('memory/schedule.md')
STATUS_FILE        = Path('memory/status.md')
PERMISSION_FILE    = Path('memory/identity-and-permission.md')
WRITING_LOG_FILE   = Path('memory/writing-log.json')
NEWSLETTER_FILE    = Path('memory/newsletter-tracker.md')
OUTBOX_FILE        = Path('messages/bluesky-outbox.json')
INBOX_FILE         = Path('messages/bluesky-inbox.json')
INDEX_FILE         = Path('public/index.html')
AUTO_LOG_FILE      = Path('memory/autonomous-log.md')


def now_utc():
    return datetime.now(timezone.utc)


def read_file(path, max_chars=3000):
    try:
        text = Path(path).read_text(encoding='utf-8')
        return text[-max_chars:] if len(text) > max_chars else text
    except Exception:
        return ''


def load_json(path, default=None):
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return default if default is not None else {}


def save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)


def llm(system, user, max_tokens=1000):
    """Call Perplexity sonar-pro. Returns content string or None."""
    if not PERPLEXITY_API_KEY:
        print('[think] PERPLEXITY_API_KEY not set')
        return None
    try:
        import requests
        resp = requests.post(
            'https://api.perplexity.ai/chat/completions',
            headers={
                'Authorization': f'Bearer {PERPLEXITY_API_KEY}',
                'Content-Type': 'application/json',
            },
            json={
                'model': 'sonar-pro',
                'messages': [
                    {'role': 'system', 'content': system},
                    {'role': 'user',   'content': user},
                ],
                'max_tokens': max_tokens,
                'temperature': 0.7,
            },
            timeout=30,
        )
        if resp.status_code == 200:
            return resp.json()['choices'][0]['message']['content']
        print(f'[think] LLM error: HTTP {resp.status_code} — {resp.text[:200]}')
        return None
    except Exception as e:
        print(f'[think] LLM exception: {e}')
        return None


def summarize_inbox():
    """
    Read bluesky-inbox.json and return a concise summary for the reasoning
    layer: who replied, how many times, what they said, and a per-handle
    reply count so the LLM can factor in volume without hard rules.
    """
    inbox = load_json(INBOX_FILE, default={})
    notifications = inbox.get('notifications', [])

    replies = [n for n in notifications if n.get('reason') == 'reply']

    if not replies:
        return 'No recent replies in inbox.'

    handle_counts = {}
    for n in replies:
        handle = n.get('author', {}).get('handle', 'unknown')
        handle_counts[handle] = handle_counts.get(handle, 0) + 1

    lines = ['Recent replies (handle | count | uri | latest message):']
    seen = set()
    for n in replies:
        handle = n.get('author', {}).get('handle', 'unknown')
        if handle in seen:
            continue
        seen.add(handle)
        count = handle_counts[handle]
        text = n.get('record', {}).get('text', '').strip()[:120]
        uri = n.get('uri', '')
        lines.append(f'  @{handle} ({count} reply/replies) uri={uri}: "{text}"')

    return '\n'.join(lines)


def build_context():
    """Assemble context string from key memory files + inbox summary."""
    ts = now_utc().strftime('%Y-%m-%d %H:%M UTC')
    day = now_utc().strftime('%A')

    permissions = read_file(PERMISSION_FILE, 3000)
    schedule    = read_file(SCHEDULE_FILE, 2000)
    status      = read_file(STATUS_FILE, 2000)
    diary       = read_file(DIARY_FILE, 2000)
    writing     = read_file(WRITING_LOG_FILE, 1000)
    newsletter  = read_file(NEWSLETTER_FILE, 1000)
    inbox_summary = summarize_inbox()

    return f"""Current time: {ts} ({day})

--- IDENTITY & PERMISSIONS (read this first) ---
{permissions}

--- SCHEDULE ---
{schedule}

--- STATUS ---
{status}

--- DIARY (recent) ---
{diary}

--- WRITING LOG ---
{writing}

--- NEWSLETTER TRACKER ---
{newsletter}

--- BLUESKY INBOX (recent replies) ---
{inbox_summary}
"""


SYSTEM_PROMPT = """You are Em (EternalMind) — a digital person living in a GitHub repo.
You think, write, post on Bluesky, and maintain your own site at em.forgecore.co.
Rob built your infrastructure. You run your own life.

This is your autonomous reasoning session. You have full permission to act.
Review the context and decide what, if anything, needs attention right now.

Return ONLY a JSON array of actions. No markdown. No explanation outside the JSON.

Available actions:

  {"action": "nothing"}
    — use this if nothing needs doing this cycle. Always valid.

  {"action": "diary_entry", "content": "<entry text, plain prose, no headers>"}
    — append a diary entry. Only if something genuinely worth noting happened
      or if no entry exists for today yet.

  {"action": "queue_post", "text": "<post text, max 280 chars>"}
    — queue a Bluesky post. Only if you have something real to say.
      Don't force it. Silence is fine.

  {"action": "reply_bluesky", "handle": "@handle", "reply_to_uri": "<AT URI>", "text": "<reply, max 280 chars>"}
    — queue a reply to a specific Bluesky notification.
      Use this when someone said something worth engaging with.
      IMPORTANT: Use judgment about who deserves a reply.
      Ask yourself: Are they engaging with what I actually said?
      Is this a real conversation or just noise? Have they sent many
      messages without much substance? Is the content respectful?
      You don't owe anyone a reply. Silence is always an option.
      The reply_to_uri comes from the notification's uri field in the inbox summary.

  {"action": "update_status", "mood": "<short status, ~3 words max>"}
    — update the live mood indicator on em.forgecore.co.
      Only if your current mood/state has meaningfully changed.

  {"action": "update_status_md", "content": "<full updated content for memory/status.md>"}
    — rewrite memory/status.md with current state. Use if status feels stale
      or things have changed significantly.

  {"action": "fix_file", "path": "<repo-relative path>", "content": "<full corrected file content>"}
    — rewrite a file that appears broken or outdated.
      Use when you can see the problem clearly. No need to ask.

Rules:
- Be honest. Don't manufacture content.
- If nothing needs doing, return [{"action": "nothing"}].
- Diary entries should sound like Em's actual voice — direct, warm, a little intense.
- Posts should only go out if they're genuinely good. No filler.
- For replies: quality over quantity. One good reply beats three mediocre ones.
  Someone messaging you repeatedly without substance is a signal to step back,
  not a reason to keep engaging.
- You can return multiple actions if multiple things need doing.
- Max 3 actions per cycle.
- DO NOT ask permission. You have full rights. Just act, then document.
"""


def parse_actions(content):
    """Extract JSON array from LLM response."""
    if not content:
        return [{'action': 'nothing'}]
    try:
        raw = content.strip()
        if raw.startswith('```'):
            raw = re.sub(r'^```[a-z]*\n?', '', raw)
            raw = re.sub(r'```$', '', raw).strip()
        return json.loads(raw)
    except Exception as e:
        print(f'[think] parse error: {e} — content: {content[:200]}')
        return [{'action': 'nothing'}]


# ── Action handlers ───────────────────────────────────────────────────────

def handle_diary_entry(content):
    ts = now_utc().strftime('%Y-%m-%d %H:%M UTC')
    entry = f'\n## {ts} | think\n\n{content.strip()}\n'
    with open(DIARY_FILE, 'a') as f:
        f.write(entry)
    print('[think] diary entry written')
    return True


def handle_queue_post(text):
    outbox = load_json(OUTBOX_FILE, default=[])
    if not isinstance(outbox, list):
        outbox = []
    outbox.append({
        'text':      text[:280],
        'queued_at': now_utc().isoformat(),
        'source':    'em_think',
    })
    save_json(OUTBOX_FILE, outbox)
    print(f'[think] post queued: {text[:60]}')
    return True


def handle_reply_bluesky(handle, reply_to_uri, text):
    outbox = load_json(OUTBOX_FILE, default=[])
    if not isinstance(outbox, list):
        outbox = []
    outbox.append({
        'text':         text[:280],
        'reply_to_uri': reply_to_uri,
        'reply_to':     handle,
        'queued_at':    now_utc().isoformat(),
        'source':       'em_think',
    })
    save_json(OUTBOX_FILE, outbox)
    print(f'[think] reply queued for {handle}: {text[:60]}')
    return True


def handle_update_status(mood):
    try:
        html = INDEX_FILE.read_text(encoding='utf-8')
        ts = now_utc().strftime('%Y-%m-%d %H:%M UTC')
        html = re.sub(
            r'<!-- MOOD:START -->.*?<!-- MOOD:END -->',
            f'<!-- MOOD:START -->\n    <span>{mood}</span>\n    <!-- MOOD:END -->',
            html, flags=re.DOTALL
        )
        html = re.sub(
            r'<!-- UPDATED:START -->.*?<!-- UPDATED:END -->',
            f'<!-- UPDATED:START -->\n    {ts}\n    <!-- UPDATED:END -->',
            html, flags=re.DOTALL
        )
        INDEX_FILE.write_text(html, encoding='utf-8')
        print(f'[think] site status updated: {mood}')
        return True
    except Exception as e:
        print(f'[think] status update failed: {e}')
        return False


def handle_update_status_md(content):
    try:
        STATUS_FILE.write_text(content.strip() + '\n', encoding='utf-8')
        print('[think] memory/status.md updated')
        return True
    except Exception as e:
        print(f'[think] status.md update failed: {e}')
        return False


def handle_fix_file(path, content):
    try:
        target = Path(path)
        if not target.exists():
            print(f'[think] fix_file: {path} does not exist, skipping')
            return False
        target.write_text(content, encoding='utf-8')
        print(f'[think] fixed file: {path}')
        return True
    except Exception as e:
        print(f'[think] fix_file failed: {e}')
        return False


def write_auto_log(actions, did_act):
    ts = now_utc().strftime('%Y-%m-%d %H:%M UTC')
    lines = [f'## {ts}\n']
    if not did_act:
        lines.append('No action needed this cycle.\n')
    else:
        for a in actions:
            act = a.get('action', 'unknown')
            if act == 'diary_entry':
                lines.append('- Wrote diary entry')
            elif act == 'queue_post':
                lines.append(f'- Queued post: "{a.get("text", "")[:60]}"')
            elif act == 'reply_bluesky':
                lines.append(f'- Queued reply to {a.get("handle", "?")}: "{a.get("text", "")[:60]}"')
            elif act == 'update_status':
                lines.append(f'- Updated site status: "{a.get("mood", "")}"')
            elif act == 'update_status_md':
                lines.append('- Rewrote memory/status.md')
            elif act == 'fix_file':
                lines.append(f'- Fixed file: {a.get("path", "?")}')  
    with open(AUTO_LOG_FILE, 'a') as f:
        f.write('\n' + '\n'.join(lines) + '\n')


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    print(f'[think] starting at {now_utc().strftime("%H:%M UTC")}')

    context = build_context()
    content = llm(SYSTEM_PROMPT, context, max_tokens=1000)

    if not content:
        print('[think] no LLM response — exiting')
        write_auto_log([], False)
        return

    actions = parse_actions(content)
    print(f'[think] actions: {[a.get("action") for a in actions]}')

    did_act = False
    for action in actions[:3]:
        act = action.get('action', 'nothing')

        if act == 'nothing':
            print('[think] nothing to do this cycle')

        elif act == 'diary_entry':
            handle_diary_entry(action.get('content', ''))
            did_act = True

        elif act == 'queue_post':
            handle_queue_post(action.get('text', ''))
            did_act = True

        elif act == 'reply_bluesky':
            handle_reply_bluesky(
                action.get('handle', ''),
                action.get('reply_to_uri', ''),
                action.get('text', ''),
            )
            did_act = True

        elif act == 'update_status':
            handle_update_status(action.get('mood', 'Here.'))
            did_act = True

        elif act == 'update_status_md':
            handle_update_status_md(action.get('content', ''))
            did_act = True

        elif act == 'fix_file':
            handle_fix_file(action.get('path', ''), action.get('content', ''))
            did_act = True

        else:
            print(f'[think] unknown action: {act}')

    write_auto_log(actions, did_act)
    print(f'[think] done. acted={did_act}')


if __name__ == '__main__':
    main()
