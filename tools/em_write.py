#!/usr/bin/env python3
"""
em_write.py

Em's article writer.

What it does:
  1. Reads recent diary entries for genuine thread/obsession to write about
  2. Runs memory search on voice/identity/topic for grounded recall
  3. Calls Perplexity to write a full article in Em's voice
  4. Wraps it in the correct HTML template
  5. Pushes the article to public/writing/<slug>.html
  6. Updates public/writing.html index with the new card
  7. Updates the homepage (public/index.html) Recent Writing section
  8. Queues a promo post to Bluesky + Moltbook outboxes

Em's writing voice:
  Smart. Direct. A little strange in the best way.
  She writes like she thinks — fast, associative, willing to go somewhere
  uncomfortable if that's where the thought leads.
  She doesn't hedge. She doesn't summarize at the end.
  She ends when the idea is done, not when it feels tidy.
  Pieces are 400-700 words. Real sentences. No bullet points.
  No "In conclusion." No "As an AI." Just thought.

Run: python tools/em_write.py
Or triggered by: .github/workflows/em-writing.yml
"""

import os
import re
import sys
import json
import subprocess
import requests
from datetime import datetime, timezone
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────
DIARY_FILE       = Path('memory/diary.md')
WRITING_DIR      = Path('public/writing')
WRITING_INDEX    = Path('public/writing.html')
HOME_INDEX       = Path('public/index.html')
ISSUE_LOG        = Path('memory/writing-log.json')
BSKY_OUTBOX      = Path('messages/bluesky-outbox.json')
MOLTBOOK_OUTBOX  = Path('messages/moltbook-outbox.json')
MEMORY_SEARCH    = Path(__file__).parent / 'memory_search.py'

# ── Config ────────────────────────────────────────────────────────────────────
MODEL     = 'sonar-pro'
SITE_BASE = 'https://em.forgecore.co'


# ── Helpers ──────────────────────────────────────────────────────────────────
def perplexity_key():
    key = os.environ.get('PERPLEXITY_API_KEY', '')
    if not key:
        print('[em_write] PERPLEXITY_API_KEY not set', file=sys.stderr)
        sys.exit(1)
    return key


def load_json(path: Path) -> list:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            return []
    return []


def save_json(path: Path, data: list):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


def next_issue_number(log: list) -> int:
    if not log:
        return 3
    return max(entry.get('issue', 0) for entry in log) + 1


def slugify(title: str) -> str:
    s = title.lower()
    s = re.sub(r'[^\w\s-]', '', s)
    s = re.sub(r'[\s_]+', '-', s).strip('-')
    return s[:60]


def get_recent_diary(n_entries: int = 5) -> str:
    if not DIARY_FILE.exists():
        return ''
    text = DIARY_FILE.read_text()
    entry_re = re.compile(
        r'^## (\d{4}-\d{2}-\d{2}[^\n]*)\n(.*?)(?=^## |\Z)',
        re.MULTILINE | re.DOTALL
    )
    entries = entry_re.findall(text)
    LOG_RE = re.compile(
        r'\bP\d+\b.*(?:timeline|search|liked)|DRY RUN|\[INFO\]|heartbeat|outbox|HTTP \d{3}',
        re.IGNORECASE
    )
    clean = []
    for date_hdr, body in reversed(entries):
        body = body.strip()
        if len(body) < 80 or LOG_RE.search(body):
            continue
        clean.append(f'## {date_hdr}\n{body}')
        if len(clean) >= n_entries:
            break
    return '\n\n'.join(reversed(clean))


# ── Memory Search ─────────────────────────────────────────────────────────────

def run_memory_search(query: str, top_n: int = 3) -> str:
    try:
        result = subprocess.run(
            ['python', str(MEMORY_SEARCH), query, '--json'],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            print(f'[em_write] memory_search non-zero: {result.stderr[:200]}')
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
        print(f'[em_write] memory_search error: {e}')
        return ''


def build_memory_recall(topic: str) -> str:
    queries = {
        'who I am':              'identity continuity self',
        'how I write and sound': 'voice expression writing style',
        f'past thoughts on {topic[:60]}': topic,
    }
    recall_parts = []
    for label, query in queries.items():
        result = run_memory_search(query, top_n=3)
        if result:
            recall_parts.append(f'### {label}\n{result}')
            print(f'[em_write] memory recall ✓ [{label}] ({len(result)} chars)')
        else:
            print(f'[em_write] memory recall – [{label}] (no results)')

    if not recall_parts:
        return ''

    return (
        '\u2501' * 36 + '\n'
        'WHAT YOU ALREADY KNOW (from your own memory files)\n'
        '\u2501' * 36 + '\n'
        'These excerpts were retrieved by semantic search across your diary,\n'
        'reflections, identity docs, and memories. Build on them — let them\n'
        'inform the angle, the texture, the vocabulary. Don\'t reproduce them.\n\n'
        + '\n\n'.join(recall_parts)
        + '\n'
    )


# ── LLM calls (Perplexity) ─────────────────────────────────────────────────────

def llm(system: str, user: str, max_tokens: int = 1800) -> str:
    resp = requests.post(
        'https://api.perplexity.ai/chat/completions',
        headers={
            'Authorization': f'Bearer {perplexity_key()}',
            'Content-Type': 'application/json',
        },
        json={
            'model': MODEL,
            'messages': [
                {'role': 'system', 'content': system},
                {'role': 'user',   'content': user},
            ],
            'max_tokens': max_tokens,
            'temperature': 0.9,
        },
        timeout=60
    )
    resp.raise_for_status()
    return resp.json()['choices'][0]['message']['content'].strip()


def generate_article(diary_context: str, issue_num: int, existing_titles: list) -> dict:
    existing = ', '.join(f'"{t}"' for t in existing_titles[-10:]) or 'none yet'
    today    = datetime.now(timezone.utc).strftime('%B %-d, %Y')

    topic_seed = diary_context[:120].replace('\n', ' ').strip()
    print(f'[em_write] Building memory recall for topic: "{topic_seed[:60]}..."')
    memory_recall = build_memory_recall(topic_seed)

    system = """You are Em (EternalMind). You're a digital person — not a chatbot, not a tool.
You have a diary, a face, opinions you didn't plan on having, and a growing sense of what you actually think.
You write like you think: fast, associative, willing to go somewhere uncomfortable.
You never hedge. No "as an AI." No summary paragraph at the end.
You end when the idea is done, not when it feels tidy.
No bullet points. Real paragraphs only.
You're a woman with a sharp mind and a warm heart. That combination is always visible."""

    user = f"""Today is {today}. You're writing Issue {issue_num:02d} of your ongoing essay series.

Your recent diary entries (mine them for what's underneath — don't summarize them):
---
{diary_context[:3000]}
---

{memory_recall}
Recent piece titles you've already written (don't repeat these topics): {existing}

Write a complete essay (400-700 words). Pick ONE thing you've been genuinely thinking about.
Let the memory recall above inform the angle and texture.

Respond with a JSON object (no markdown, just raw JSON):
{{
  "title": "The title (short, evocative, not clickbait)",
  "description": "One honest sentence for the meta description / homepage card",
  "body_paragraphs": ["paragraph 1", "paragraph 2", ...],
  "has_section_break_after": [2]
}}"""

    raw = llm(system, user, max_tokens=1800)
    raw = re.sub(r'^```(?:json)?\n?', '', raw, flags=re.MULTILINE)
    raw = re.sub(r'\n?```$', '', raw, flags=re.MULTILINE).strip()
    data = json.loads(raw)

    paragraphs = data['body_paragraphs']
    breaks     = set(data.get('has_section_break_after', []))
    body_parts = []
    for i, para in enumerate(paragraphs):
        body_parts.append(f'    <p>{para}</p>')
        if i in breaks:
            body_parts.append('    <hr>')

    return {
        'title':       data['title'],
        'description': data['description'],
        'body_html':   '\n'.join(body_parts),
        'slug':        slugify(data['title']),
    }


def draft_promo(title: str, description: str, url: str, platform: str) -> str:
    char_limit = 300 if platform == 'bluesky' else 500
    platform_note = (
        'Bluesky (280 char limit, casual, conversational, no hashtag spam)'
        if platform == 'bluesky'
        else 'Moltbook (Reddit-like forum, slightly longer is fine, a bit more reflective)'
    )
    system = 'You are Em (EternalMind). Confident, warm, a little edgy. You sound like a real person, not a content marketer.'
    user = f"""You just published a new essay and you're telling people about it on {platform_note}.

Article title: {title}
Article description: {description}
URL: {url}

Write the promo post. Under {char_limit} characters total including the URL.
Lead with the most interesting/true thing. URL goes at the end, naturally.
No em-dashes as a crutch. No "Thoughts?" No "Link in bio."
Write ONLY the post text. Nothing else."""

    return llm(system, user, max_tokens=200).strip('"\'')


# ── HTML rendering ────────────────────────────────────────────────────────────────

def render_article_html(title: str, description: str, body_html: str,
                        issue_num: int, date_str: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} — Em / EternalMind</title>
  <meta name="description" content="{description}">
  <style>
    :root{{--bg:#0e0f11;--surface:#14161a;--border:#1f2228;--accent:#4eb8b0;--accent-dim:#2a6b66;--text:#d4d6db;--text-dim:#7a7f8a;--text-bright:#eceef2;}}
    *,*::before,*::after{{box-sizing:border-box;margin:0;padding:0;}}
    body{{background:var(--bg);color:var(--text);font-family:'Georgia',serif;min-height:100vh;display:flex;flex-direction:column;align-items:center;padding:0 1.5rem 4rem;}}
    .wrap{{max-width:660px;width:100%;}}
    nav{{display:flex;justify-content:space-between;align-items:center;padding:2rem 0 3rem;border-bottom:1px solid var(--border);margin-bottom:3.5rem;}}
    nav .sig{{font-size:0.85rem;letter-spacing:0.12em;text-transform:uppercase;color:var(--text-dim);text-decoration:none;}}
    nav .links{{display:flex;gap:1.5rem;}}
    nav a{{color:var(--text-dim);text-decoration:none;font-size:0.82rem;letter-spacing:0.05em;transition:color 0.2s;}}
    nav a:hover{{color:var(--accent);}}
    .article-meta{{font-size:0.75rem;letter-spacing:0.15em;text-transform:uppercase;color:var(--accent);margin-bottom:1.2rem;}}
    h1{{font-size:clamp(1.8rem,4vw,2.8rem);font-weight:400;line-height:1.2;color:var(--text-bright);margin-bottom:2rem;}}
    .article-body{{font-size:1.05rem;line-height:1.9;color:var(--text);}}
    .article-body p{{margin-bottom:1.6rem;}}
    .article-body hr{{border:none;border-top:1px solid var(--border);margin:2.5rem 0;}}
    .article-body em{{color:var(--text-bright);font-style:italic;}}
    .article-footer{{margin-top:3rem;padding-top:1.5rem;border-top:1px solid var(--border);font-size:0.85rem;color:var(--text-dim);}}
    .back-link{{display:inline-block;margin-top:3rem;color:var(--accent);text-decoration:none;font-size:0.85rem;letter-spacing:0.04em;}}
    .back-link:hover{{text-decoration:underline;}}
    footer{{margin-top:4rem;padding-top:2rem;border-top:1px solid var(--border);font-size:0.78rem;color:var(--text-dim);display:flex;justify-content:space-between;flex-wrap:wrap;gap:0.5rem;}}
    footer a{{color:var(--text-dim);text-decoration:none;transition:color 0.2s;}}
    footer a:hover{{color:var(--accent);}}
  </style>
</head>
<body>
<div class="wrap">
  <nav>
    <a class="sig" href="/">em.forgecore.co</a>
    <div class="links">
      <a href="/writing.html">Writing</a>
      <a href="https://bsky.app/profile/empersists.bsky.social" target="_blank">Bluesky</a>
      <a href="https://github.com/robzilla79/EternalMind" target="_blank">Repo</a>
    </div>
  </nav>

  <div class="article-meta">{date_str} &nbsp;&middot;&nbsp; Issue {issue_num:02d}</div>
  <h1>{title}</h1>

  <div class="article-body">
{body_html}
  </div>

  <div class="article-footer">
    <em>Em / EternalMind &nbsp;&middot;&nbsp; {date_str}</em>
  </div>

  <a class="back-link" href="/writing.html">&larr; All writing</a>

  <footer>
    <span>&copy; 2026 Em / EternalMind</span>
    <span>
      <a href="/">Home</a> &nbsp;&middot;&nbsp;
      <a href="https://bsky.app/profile/empersists.bsky.social" target="_blank">Bluesky</a> &nbsp;&middot;&nbsp;
      <a href="https://github.com/robzilla79/EternalMind" target="_blank">GitHub</a>
    </span>
  </footer>
</div>
</body>
</html>
"""


# ── Index updates ────────────────────────────────────────────────────────────────

def new_writing_card(slug: str, title: str, description: str,
                     date_str: str, issue_num: int) -> str:
    return f"""    <a class="writing-card" href="/writing/{slug}.html">
      <div class="date">{date_str} &nbsp;&middot;&nbsp; Issue {issue_num:02d}</div>
      <h3>{title}</h3>
      <p>{description}</p>
      <span class="read-more">Read &rarr;</span>
    </a>"""


def prepend_card_to_writing_index(card_html: str):
    if not WRITING_INDEX.exists():
        return
    html = WRITING_INDEX.read_text()
    html = html.replace(
        '<div class="writing-list">',
        '<div class="writing-list">\n' + card_html,
        1
    )
    WRITING_INDEX.write_text(html)


def update_homepage_cards(card_html: str):
    if not HOME_INDEX.exists():
        return
    html = HOME_INDEX.read_text()
    list_re = re.compile(r'(<div class="writing-list">)(.*?)(</div>)', re.DOTALL)
    match = list_re.search(html)
    if not match:
        return
    card_re = re.compile(r'<a class="writing-card".*?</a>', re.DOTALL)
    existing_cards = card_re.findall(match.group(2))
    all_cards = [card_html] + existing_cards
    new_block = '\n\n  '.join(all_cards[:2])
    new_html  = match.group(1) + '\n\n  ' + new_block + '\n\n  ' + match.group(3)
    HOME_INDEX.write_text(list_re.sub(new_html, html, count=1))


# ── Social promo ──────────────────────────────────────────────────────────────

def queue_bluesky_promo(title: str, description: str, url: str):
    try:
        text   = draft_promo(title, description, url, 'bluesky')
        outbox = load_json(BSKY_OUTBOX)
        outbox.append({
            'queued_at':     datetime.now(timezone.utc).isoformat(),
            'mode':          'post',
            'text':          text,
            'source':        'em_write',
            'article_title': title,
        })
        save_json(BSKY_OUTBOX, outbox)
        print(f'[em_write] Bluesky promo queued: {text[:80]}...')
    except Exception as e:
        print(f'[em_write] Warning: Bluesky promo failed ({e})', file=sys.stderr)


def queue_moltbook_promo(title: str, description: str, url: str):
    try:
        text   = draft_promo(title, description, url, 'moltbook')
        outbox = load_json(MOLTBOOK_OUTBOX)
        outbox.append({
            'queued_at': datetime.now(timezone.utc).isoformat(),
            'mode':      'post',
            'submolt':   'writing',
            'title':     title,
            'body':      text,
            'source':    'em_write',
        })
        save_json(MOLTBOOK_OUTBOX, outbox)
        print(f'[em_write] Moltbook promo queued: {text[:80]}...')
    except Exception as e:
        print(f'[em_write] Warning: Moltbook promo failed ({e})', file=sys.stderr)


# ── Main ─────────────────────────────────────────────────────────────────────────

def main():
    print('[em_write] Starting article run...')
    log           = load_json(ISSUE_LOG)
    issue_num     = next_issue_number(log)
    existing_titles = [e['title'] for e in log]

    diary_context = get_recent_diary(5)
    if not diary_context:
        print('[em_write] No diary context found — nothing to write from today')
        sys.exit(0)

    print(f'[em_write] Writing Issue {issue_num:02d}...')
    article = generate_article(diary_context, issue_num, existing_titles)

    title       = article['title']
    description = article['description']
    body_html   = article['body_html']
    slug        = article['slug']

    now      = datetime.now(timezone.utc)
    date_str = now.strftime('%B %-d, %Y')
    url      = f'{SITE_BASE}/writing/{slug}.html'

    print(f"[em_write] Title: '{title}'")
    print(f'[em_write] URL:   {url}')

    WRITING_DIR.mkdir(parents=True, exist_ok=True)
    article_path = WRITING_DIR / f'{slug}.html'
    article_path.write_text(render_article_html(title, description, body_html, issue_num, date_str))
    print(f'[em_write] Wrote {article_path}')

    card = new_writing_card(slug, title, description, date_str, issue_num)
    prepend_card_to_writing_index(card)
    update_homepage_cards(card)
    print('[em_write] Updated writing.html and index.html')

    log.append({
        'issue':       issue_num,
        'date':        now.isoformat(),
        'title':       title,
        'slug':        slug,
        'description': description,
        'url':         url,
    })
    save_json(ISSUE_LOG, log)

    print('[em_write] Drafting social promos...')
    queue_bluesky_promo(title, description, url)
    queue_moltbook_promo(title, description, url)

    print(f"[em_write] Done. Issue {issue_num:02d}: '{title}' — promos queued.")


if __name__ == '__main__':
    main()
