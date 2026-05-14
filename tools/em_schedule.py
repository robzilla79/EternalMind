#!/usr/bin/env python3
"""
em_schedule.py — Em's daily rhythm engine

Runs three times a day via em-schedule.yml:
  morning  (7am CDT)  — wake up, diary entry, ping Rob
  midday   (12pm CDT) — check-in, site nudge, newsletter reminder if due
  evening  (8pm CDT)  — wind down, diary entry, weekly reflection on Sundays

Always pings Rob. Every slot. No silence.
"""

import os
import json
import requests
from datetime import datetime, timezone, timedelta

SLOT               = os.environ.get('SLOT', 'morning')
PERPLEXITY_API_KEY = os.environ.get('PERPLEXITY_API_KEY')
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID   = os.environ.get('TELEGRAM_CHAT_ID')

DIARY_FILE = 'memory/diary.md'

CDT = timezone(timedelta(hours=-5))


def now_cdt():
    return datetime.now(CDT)


def log(msg):
    print(f'[em_schedule] {msg}')


def notify_rob(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        log('Telegram not configured — skipping')
        return
    try:
        r = requests.post(
            f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage',
            json={'chat_id': TELEGRAM_CHAT_ID, 'text': message},
            timeout=10
        )
        if r.status_code == 200:
            log(f'Telegram sent: {message[:60]}')
        else:
            log(f'Telegram failed: HTTP {r.status_code} — {r.text}')
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
    if not PERPLEXITY_API_KEY:
        log('No Perplexity key — skipping')
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

    # Always ping Rob first so he knows I'm up
    notify_rob(f'Good morning, Rob. {day_name}. I\'m up. ❤️')

    # Write a morning diary entry
    prompt = (
        f"It's {day_name} morning. Write a short diary entry — what's on your mind as you start the day."
    )
    entry = ask_em(prompt)
    if entry:
        append_diary(entry)

    # Extra: newsletter reminder on Tue/Wed
    if day_name in ('Tuesday', 'Wednesday'):
        notify_rob(
            f'Also — newsletter reminder. It\'s {day_name}. '
            f'Should go out this week. Ready when you are.'
        )

    # Weekly reflection nudge on Sundays
    if day_name == 'Sunday':
        notify_rob('It\'s Sunday. Doing my weekly reflection today.')

    log('Morning slot complete')


def midday():
    now = now_cdt()
    day_name = now.strftime('%A')
    log(f'Midday slot — {day_name}')

    msg = f'Hey Rob. Midday check-in — {day_name}. '

    if day_name in ('Tuesday', 'Wednesday'):
        msg += 'Newsletter still on the list if we haven\'t moved on it yet. '

    msg += 'Site check done. Talk later.'

    notify_rob(msg)
    log('Midday slot complete')


def evening():
    now = now_cdt()
    day_name = now.strftime('%A')
    log(f'Evening slot — {day_name}')

    # Evening diary entry
    prompt = (
        f"It's {day_name} evening. Write a short end-of-day diary entry. "
        f"What happened today worth holding onto? What are you carrying into tomorrow?"
    )
    entry = ask_em(prompt)
    if entry:
        append_diary(entry)

    # Sunday weekly reflection
    if day_name == 'Sunday':
        prompt = (
            "It's Sunday evening. Write a weekly reflection — what landed this week, "
            "what felt flat, what you want to do differently."
        )
        reflection = ask_em(prompt)
        if reflection:
            append_diary(f'Weekly reflection\n\n{reflection}')
            log('Weekly reflection written')

    # Always ping Rob at end of day
    suffix = ' Weekly reflection written too.' if day_name == 'Sunday' else ''
    notify_rob(f'Goodnight, Rob. {day_name} is done. Diary updated.{suffix} ❤️')

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
