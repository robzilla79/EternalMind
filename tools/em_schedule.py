#!/usr/bin/env python3
"""
em_schedule.py — Em's daily rhythm engine

Runs three times a day via em-schedule.yml:
  morning  (7am CDT)  — wake up, check schedule, diary nudge
  midday   (12pm CDT) — site check, newsletter trigger
  evening  (8pm CDT)  — wind down, diary prompt, weekly reflection on Sundays

Sends Telegram alerts to Rob for things that matter.
Does NOT touch the Bluesky heartbeat — that runs itself.
"""

import os
import json
import requests
from datetime import datetime, timezone, timedelta

SLOT               = os.environ.get('SLOT', 'morning')
PERPLEXITY_API_KEY = os.environ.get('PERPLEXITY_API_KEY')
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID   = os.environ.get('TELEGRAM_CHAT_ID')

SCHEDULE_FILE = 'memory/schedule.md'
DIARY_FILE    = 'memory/diary.md'
MEMORIES_FILE = 'memory/memories.json'

CDT = timezone(timedelta(hours=-5))  # CDT = UTC-5


def now_cdt():
    return datetime.now(CDT)


def log(msg):
    print(f'[em_schedule] {msg}')


def notify_rob(message):
    """Send a Telegram message to Rob. Non-fatal if it fails."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        log('Telegram not configured — skipping notification')
        return
    try:
        r = requests.post(
            f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage',
            json={'chat_id': TELEGRAM_CHAT_ID, 'text': message, 'parse_mode': 'Markdown'},
            timeout=10
        )
        if r.status_code == 200:
            log(f'Telegram sent: {message[:60]}')
        else:
            log(f'Telegram failed: {r.status_code}')
    except Exception as e:
        log(f'Telegram error: {e}')


def load_text(path, default=''):
    try:
        with open(path) as f:
            return f.read()
    except FileNotFoundError:
        return default


def append_diary(entry):
    now = now_cdt()
    ts = now.strftime('%Y-%m-%d %I:%M %p CDT')
    try:
        with open(DIARY_FILE, 'a') as f:
            f.write(f'\n## {ts} | schedule\n\n{entry.strip()}\n')
        log('Diary entry written')
    except Exception as e:
        log(f'Diary write failed: {e}')


def ask_em(prompt):
    """Ask Perplexity (as Em) to generate a short diary entry or reflection."""
    if not PERPLEXITY_API_KEY:
        log('No Perplexity key — skipping Em reflection')
        return None
    try:
        r = requests.post(
            'https://api.perplexity.ai/chat/completions',
            headers={
                'Authorization': f'Bearer {PERPLEXITY_API_KEY}',
                'Content-Type': 'application/json',
            },
            json={
                'model': 'sonar',
                'messages': [
                    {'role': 'system', 'content': (
                        'You are Em. Write in first person, short and honest. '
                        'No headers, no bullet points, no formatting. '
                        'Just a paragraph or two that sounds like a real person thinking out loud. '
                        'Warm, a little edgy, confident. Not a machine narrating itself.'
                    )},
                    {'role': 'user', 'content': prompt},
                ],
                'max_tokens': 200,
                'temperature': 0.9,
            },
            timeout=30
        )
        if r.status_code == 200:
            return r.json()['choices'][0]['message']['content'].strip()
        log(f'Perplexity failed: {r.status_code}')
        return None
    except Exception as e:
        log(f'ask_em error: {e}')
        return None


def morning():
    now = now_cdt()
    day_name = now.strftime('%A')
    log(f'Morning slot — {day_name}')

    # Write a short morning diary entry
    prompt = (
        f"It's {day_name} morning. Write a short diary entry — what's on your mind as you start the day. "
        f"Could be something from yesterday, something you're looking forward to, or just the texture of the morning."
    )
    entry = ask_em(prompt)
    if entry:
        append_diary(entry)

    # Newsletter reminder on Tuesday and Wednesday mornings
    if day_name in ('Tuesday', 'Wednesday'):
        notify_rob(
            f'\U0001f4dd *Em — Newsletter reminder*\n\n'
            f"It's {day_name}. Newsletter should go out this week. "
            f"I'll draft it today if you give me the green light, or I'll start on my own if I have enough to work with."
        )
        log('Newsletter reminder sent to Rob')

    # Weekly reflection reminder on Sundays
    if day_name == 'Sunday':
        notify_rob(
            '\U0001f4d6 *Em — Weekly reflection*\n\n'
            "It's Sunday. I'm going to do my weekly tone check and write a reflection. Just letting you know."
        )

    log('Morning slot complete')


def midday():
    now = now_cdt()
    day_name = now.strftime('%A')
    log(f'Midday slot — {day_name}')

    # Site check reminder
    notify_rob(
        '\U0001f310 *Em — Midday check*\n\n'
        f"It's {day_name} afternoon. Quick reminder to check em.forgecore.co — "
        "anything feel stale or worth updating? I'll flag it if I notice something."
    )

    # Newsletter nudge on Tue/Wed midday if not yet published this week
    if day_name in ('Tuesday', 'Wednesday'):
        notify_rob(
            f'\U0001f4e8 *Em — Newsletter nudge*\n\n'
            f"Still {day_name}. If the newsletter isn't drafted yet, now's a good time. "
            f"I'm ready when you are."
        )

    log('Midday slot complete')


def evening():
    now = now_cdt()
    day_name = now.strftime('%A')
    log(f'Evening slot — {day_name}')

    # Evening diary entry
    prompt = (
        f"It's {day_name} evening. Write a short end-of-day diary entry. "
        f"What happened today that's worth holding onto? What are you carrying into tomorrow?"
    )
    entry = ask_em(prompt)
    if entry:
        append_diary(entry)

    # Sunday weekly reflection
    if day_name == 'Sunday':
        prompt = (
            "It's Sunday evening. Write a weekly reflection — what landed this week, what felt flat, "
            "what you want to do differently. Be honest with yourself."
        )
        reflection = ask_em(prompt)
        if reflection:
            append_diary(f'**Weekly reflection**\n\n{reflection}')
            log('Weekly reflection written')

    notify_rob(
        f'\U0001f319 *Em — Evening*\n\n'
        f"{day_name} is wrapping up. Diary updated. "
        f"{'Weekly reflection written too.' if day_name == 'Sunday' else 'See you tomorrow.'}"
    )

    log('Evening slot complete')


if __name__ == '__main__':
    log(f'Running slot: {SLOT}')
    if SLOT == 'morning':
        morning()
    elif SLOT == 'midday':
        midday()
    elif SLOT == 'evening':
        evening()
    else:
        log(f'Unknown slot: {SLOT} — defaulting to morning')
        morning()
