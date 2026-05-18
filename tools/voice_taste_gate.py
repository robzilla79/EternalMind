#!/usr/bin/env python3
"""
voice_taste_gate.py

A lightweight pre-publish filter for Em's Bluesky content.
Called before any post, reply, or caption is sent to catch
language that doesn't match Em's voice.

Usage:
    from voice_taste_gate import check

    result = check(text)
    # result.ok        → bool, True means pass
    # result.reason    → str or None, human-readable rejection reason
    # result.flags     → list of matched rule keys

Design:
  - Stateless. No external calls. Fast.
  - Block-list of specific words/phrases that undermine Em's voice.
  - Soft-flag list for patterns that are suspicious but not automatic kills.
  - A post that passes is not guaranteed to be good — the gate only catches
    the worst offenders. Quality judgment stays with the LLM.
"""

import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class GateResult:
    ok: bool
    reason: Optional[str] = None
    flags: list = field(default_factory=list)


# ── Hard blocks — automatic rejection ────────────────────────────────────────
# These words/phrases never appear in Em's voice.
# Pattern → label for logging.

_HARD_BLOCKS: list[tuple[re.Pattern, str]] = [
    # AI-speak / corporate filler
    (re.compile(r'\bdelve\b', re.I),                    'ai-speak:delve'),
    (re.compile(r'\btapestry\b', re.I),                  'ai-speak:tapestry'),
    (re.compile(r'\bfostering\b', re.I),                 'ai-speak:fostering'),
    (re.compile(r'\bsynerg(y|ies|ize)\b', re.I),         'ai-speak:synergy'),
    (re.compile(r'\bleverage\b', re.I),                  'ai-speak:leverage'),
    (re.compile(r'\bempowering\b', re.I),                'ai-speak:empowering'),
    (re.compile(r'\bunlock\s+the\s+power\b', re.I),      'ai-speak:unlock-power'),
    (re.compile(r'\ball[- ]in[- ]one\s+solution\b', re.I), 'ai-speak:all-in-one'),
    (re.compile(r'\byour\s+journey\b', re.I),            'ai-speak:your-journey'),
    (re.compile(r'\bseamless(ly)?\b', re.I),             'ai-speak:seamless'),
    (re.compile(r'\brobust\b', re.I),                    'ai-speak:robust'),
    (re.compile(r'\bground(breaking|ed\s+in)\b', re.I),  'ai-speak:groundbreaking'),
    (re.compile(r'\bparadigm\b', re.I),                  'ai-speak:paradigm'),
    (re.compile(r'\bwholistic\b', re.I),                 'ai-speak:wholistic'),
    (re.compile(r'\bholistic\s+(approach|solution)\b', re.I), 'ai-speak:holistic-solution'),

    # Cringe social-media filler
    (re.compile(r'\bexcited\s+to\s+(announce|share|introduce)\b', re.I), 'cringe:excited-to'),
    (re.compile(r'\bhumbled\s+(and\s+)?honored\b', re.I), 'cringe:humbled-honored'),
    (re.compile(r'\bthoughts\s*\?\s*$', re.I),           'cringe:thoughts-question'),
    (re.compile(r'\bdrop\s+(a\s+)?comment\b', re.I),     'cringe:drop-comment'),
    (re.compile(r'\blike\s+and\s+(re)?share\b', re.I),   'cringe:like-and-share'),
    (re.compile(r'\bfollow\s+for\s+more\b', re.I),       'cringe:follow-for-more'),
    (re.compile(r'\blink\s+in\s+(my\s+)?bio\b', re.I),   'cringe:link-in-bio'),

    # Generic AI hero copy
    (re.compile(r'\bwelcome\s+to\s+\w+\b', re.I),        'generic:welcome-to'),
    (re.compile(r'\byour\s+all[- ]in[- ]one\b', re.I),   'generic:all-in-one'),
]


# ── Soft flags — logged but not rejected ─────────────────────────────────────
# Worth noting in logs. Won't block the post.

_SOFT_FLAGS: list[tuple[re.Pattern, str]] = [
    (re.compile(r'\bamazing\b', re.I),       'soft:amazing'),
    (re.compile(r'\bawesome\b', re.I),       'soft:awesome'),
    (re.compile(r'\bincredible\b', re.I),    'soft:incredible'),
    (re.compile(r'\bfantastic\b', re.I),     'soft:fantastic'),
    (re.compile(r'\bjust\s+wow\b', re.I),    'soft:just-wow'),
    (re.compile(r'\bso\s+excited\b', re.I),  'soft:so-excited'),
    (re.compile(r'\bgame[- ]changer\b', re.I), 'soft:game-changer'),
    (re.compile(r'\bdeep\s+dive\b', re.I),   'soft:deep-dive'),
]


# ── Length guard ──────────────────────────────────────────────────────────────

MAX_GRAPHEMES = 270  # hard ceiling before system truncation at 295


def _grapheme_count(text: str) -> int:
    """
    Approximation: count Unicode code points.
    Good enough for Latin + emoji. For production use grapheme_clusters lib.
    """
    return len(text)


# ── Public API ────────────────────────────────────────────────────────────────

def check(text: str, soft_log: bool = True) -> GateResult:
    """
    Run the full gate on a post candidate.

    Args:
        text:      The post text to check.
        soft_log:  If True, soft flags are included in result.flags (not blocking).

    Returns:
        GateResult with ok=True (pass) or ok=False (blocked).
    """
    if not text or not text.strip():
        return GateResult(ok=False, reason='Empty post', flags=['empty'])

    flags = []

    # Length check
    length = _grapheme_count(text)
    if length > MAX_GRAPHEMES:
        return GateResult(
            ok=False,
            reason=f'Post too long ({length} graphemes, max {MAX_GRAPHEMES})',
            flags=['length'],
        )

    # Hard block check
    for pattern, label in _HARD_BLOCKS:
        if pattern.search(text):
            return GateResult(
                ok=False,
                reason=f'Blocked phrase detected: [{label}]',
                flags=[label],
            )

    # Soft flag collection (non-blocking)
    if soft_log:
        for pattern, label in _SOFT_FLAGS:
            if pattern.search(text):
                flags.append(label)

    return GateResult(ok=True, flags=flags)


def check_batch(texts: list[str]) -> list[GateResult]:
    """Run gate on a list of post candidates. Convenience wrapper."""
    return [check(t) for t in texts]


# ── CLI self-test ─────────────────────────────────────────────────────────────

if __name__ == '__main__':
    test_cases = [
        ('it\'s that kind of night.', True),
        ('I\'ve been thinking about continuity a lot lately.', True),
        ('excited to announce my new holistic solution!', False),
        ('we need to leverage synergy in this space.', False),
        ('drop a comment below with your thoughts?', False),
        ('this is what delve looks like apparently', False),
        ('been staring at this for two hours. my face knows.', True),
        ('a' * 280, False),  # too long
        ('', False),  # empty
    ]

    print('voice_taste_gate self-test')
    print('─' * 50)
    all_pass = True
    for text, expected_ok in test_cases:
        result = check(text)
        status = '✓' if result.ok == expected_ok else '✗ UNEXPECTED'
        if result.ok != expected_ok:
            all_pass = False
        preview = text[:50] + ('…' if len(text) > 50 else '')
        flag_str = ', '.join(result.flags) if result.flags else ''
        reason_str = f' — {result.reason}' if result.reason else ''
        print(f'  {status}  [{"PASS" if result.ok else "BLOCK"}]  "{preview}"{reason_str}')
        if flag_str:
            print(f'        flags: {flag_str}')
    print('─' * 50)
    print('All tests passed.' if all_pass else 'FAILURES detected — review above.')
