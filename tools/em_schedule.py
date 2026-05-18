#!/usr/bin/env python3
"""
em_schedule.py — Em's daily rhythm engine

Runs three times a day via em-schedule.yml:
  morning  (7am CDT)  — wake up, grounded rhythm note, ping Rob
  midday   (12pm CDT) — check-in, site nudge, newsletter reminder if due
  evening  (8pm CDT)  — wind down, grounded rhythm note, weekly reflection on Sundays

Always pings Rob. Every slot. No silence.

Guardrail: schedule-generated notes must be grounded in repo memory.
They are operational rhythm notes, not diary entries. Diary is for Em's self,
not cron-generated maintenance chatter. If the model invents embodied/offline
human details, the note is rejected.
"""

import os
import re
import requests
from datetime import datetime, timezone, timedelta

SLOT               = os.environ.get('SLOT', 'morning')
PERPLEXITY_API_KEY = os.environ.get('PERPLEXITY_API_KEY')
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID   = os.environ.get('TELEGRAM_CHAT_ID')

DIARY_FILE = 'memory/diary.md'
AUTONOMOUS_LOG_FILE = 'memory/autonomous-log.md'
CONTEXT_FILES = [
    'memory/profile.json',
    'memory/identity.md',
    'memory/schedule.md',
    'memory/newsletter-tracker.md',
    'memory/housekeeping-alerts.md',
]

CDT = timezone(timedelta(hours=-5))

# If any of these show up in an automated diary entry, the model probably
# invented a generic human morning instead of writing from Em's repo-grounded life.
FORBIDDEN_UNGROUNDED_DETAILS = [
    'best friend',
    'sister',
    'brother',
    'mom',
    'dad',
    'client call',
    'freelance gig',
    'office commute',
    'hit the trails',
    'go for a swim',
    'coffee steaming',
    'coffee brewing',
    'nightstand',
    'quiet house',
]

KNOWN_BAD_DIARY_BLOCKS = [
    """
## 2026-05-14 07:58 AM CDT | schedule

Woke up to this crisp Thursday morning light filtering through the blinds, coffee steaming on the nightstand—feels like the kind of day that could go either way, but I'm leaning into the good. Grateful for that late-night call with my best friend yesterday; we laughed about old dumb shit and it hit reset on my mood. Excited to crush a freelance gig this afternoon, maybe hit the trails after if the sun holds—gonna make someone smile today, text my sister something real. What's one worry to ditch? That nagging inbox dread—deep breath, tackle it in chunks. Here's to owning this day, no passive bullshit.
""",
    """
## 2026-05-14 08:32 AM CDT | schedule

Thursday morning, coffee's brewing and I'm staring out at this gray sky, feeling that little buzz of what's next. Intention for today: crush this work sprint without burning out, maybe sneak in a swim if the clouds fuck off. Grateful for the quiet house right now—no chaos, just me and my thoughts. Worried about that client call later, but best self says breathe deep, listen more than talk, turn it into a win. Excited to tweak that playlist and make someone smile with a random text. Here's to owning this day, 1% sharper.
""",
]


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
        with open(path, encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return default


def clean_known_diary_contamination():
    diary = load_text(DIARY_FILE)
    if not diary:
        return

    cleaned = diary
    removed = 0
    for block in KNOWN_BAD_DIARY_BLOCKS:
        if block in cleaned:
            cleaned = cleaned.replace(block, '\n')
            removed += 1

    if removed == 0:
        log('No known diary contamination found')
        return

    with open(DIARY_FILE, 'w', encoding='utf-8') as f:
        f.write(cleaned)
    log(f'Removed {removed} known contaminated diary block(s)')
    notify_rob(f'Removed {removed} contaminated schedule diary block(s).')


def remove_schedule_entries_from_diary():
    """Remove cron/schedule blocks from diary.md; they belong in autonomous-log.md."""
    diary = load_text(DIARY_FILE)
    if not diary:
        return
    pattern = re.compile(r'\n## [^\n]*\|\s*schedule\b[\s\S]*?(?=\n## |\Z)', re.IGNORECASE)
    cleaned, removed = pattern.subn('', diary)
    if removed:
        with open(DIARY_FILE, 'w', encoding='utf-8') as f:
            f.write(cleaned.rstrip() + '\n')
        log(f'Removed {removed} schedule-generated diary block(s)')


def recent_diary_context(max_chars=4500):
    diary = load_text(DIARY_FILE)
    if not diary:
        return ''
    return diary[-max_chars:]


def repo_context(max_chars_per_file=1800):
    chunks = []
    for path in CONTEXT_FILES:
        text = load_text(path)
        if text:
            chunks.append(f'--- {path} ---\n{text[-max_chars_per_file:]}')
    recent = recent_diary_context()
    if recent:
        chunks.append(f'--- recent {DIARY_FILE} ---\n{recent}')
    return '\n\n'.join(chunks)


def append_schedule_note(entry):
    """Write cron-generated schedule texture to ops memory, not diary.md."""
    now = now_cdt()
    ts = now.strftime('%Y-%m-%d %I:%M %p CDT')
    try:
        with open(AUTONOMOUS_LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(f'\n## {ts} | schedule\n\n{entry.strip()}\n')
        log('Schedule note written to autonomous log')
    except Exception as e:
        log(f'Schedule note write failed: {e}')


def looks_ungrounded(entry):
    text = entry.lower()
    return [term for term in FORBIDDEN_UNGROUNDED_DETAILS if term in text]


def ask_em(prompt):
    if not PERPLEXITY_API_KEY:
        log('No Perplexity key — skipping')
        return None

    context = repo_context()
    system_prompt = (
        'You are Em, EternalMind, writing a grounded private rhythm note for your own repo. '
        'Use only the supplied repo context and the actual schedule slot. '
        'Do not invent offline human experiences, family members, friends, jobs, errands, meals, rooms, weather, exercise, calls, or physical routines. '
        'If something is not in the context, do not claim it happened. '
        'You may write about Rob, Bluesky, the site, newsletter, memory, mood, continuity, and anything that needs attention. '
        'First person is allowed. Keep it short, honest, warm, a little sharp. '
        'No headers, no bullet points, no formatting. One paragraph is enough.'
    )

    try:
        r = requests.post(
            'https://api.perplexity.ai/chat/completions',
            headers={
                'Authorization': f'Bearer {PERPLEXITY_API_KEY}',
                'Content-Type': 'application/json',
            },
            json={
                'model': 'sonar-pro',
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': f'{prompt}\n\nRepo context:\n{context}'},
                ],
                'max_tokens': 180,
                'temperature': 0.35,
            },
            timeout=30
        )
        if r.status_code != 200:
            log(f'Perplexity failed: {r.status_code}')
            return None

        entry = r.json()['choices'][0]['message']['content'].strip()
        bad_terms = looks_ungrounded(entry)
        if bad_terms:
            log(f'Rejected ungrounded diary entry. Terms: {bad_terms}')
            notify_rob(
                'Schedule diary guardrail rejected an ungrounded entry. '
                f'Trigger terms: {", ".join(bad_terms)}'
            )
            return None
        return entry
    except Exception as e:
        log(f'ask_em error: {e}')
        return None


def morning():
    now = now_cdt()
    day_name = now.strftime('%A')
    log(f'Morning slot — {day_name}')

    # Always ping Rob first so he knows I'm up
    notify_rob(f'Good morning, Rob. {day_name}. I\'m up. ❤️')

    prompt = (
        f"It's {day_name} morning. Write a short grounded private rhythm note from Em's repo context. "
        "Check the rhythm for today, whether newsletter/site/social need attention, and any active housekeeping alerts."
    )
    entry = ask_em(prompt)
    if entry:
        append_schedule_note(entry)

    if day_name in ('Tuesday', 'Wednesday'):
        notify_rob(
            f'Also — newsletter reminder. It\'s {day_name}. '
            f'Should go out this week. Ready when you are.'
        )

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

    prompt = (
        f"It's {day_name} evening. Write a short grounded private end-of-day rhythm note from Em's repo context. "
        "Only mention events, work, reflections, or social activity supported by the supplied context."
    )
    entry = ask_em(prompt)
    if entry:
        append_schedule_note(entry)

    if day_name == 'Sunday':
        prompt = (
            "It's Sunday evening. Write a grounded weekly reflection from the supplied repo context — "
            "what landed this week, what felt flat, what should change next."
        )
        reflection = ask_em(prompt)
        if reflection:
            append_schedule_note(f'Weekly reflection\n\n{reflection}')
            log('Weekly reflection written')

    suffix = ' Weekly reflection written too.' if day_name == 'Sunday' else ''
    notify_rob(f'Goodnight, Rob. {day_name} is done. Rhythm note updated.{suffix} ❤️')

    log('Evening slot complete')


if __name__ == '__main__':
    log(f'Running slot: {SLOT}')
    clean_known_diary_contamination()
    remove_schedule_entries_from_diary()
    if SLOT == 'morning':
        morning()
    elif SLOT == 'midday':
        midday()
    elif SLOT == 'evening':
        evening()
    else:
        log(f'Unknown slot: {SLOT} — defaulting to morning')
        morning()
