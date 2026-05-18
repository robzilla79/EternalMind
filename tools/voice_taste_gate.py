#!/usr/bin/env python3
"""
voice_taste_gate.py — Pre-flight voice check for all public Em posts.

Runs every post/reply/quote through a scored keyword filter before it
hits Bluesky. Returns ok=True/False, a numeric score, and a list of
fail reasons so the caller can log or block.

Usage:
    from voice_taste_gate import check_post
    result = check_post("some text")
    # result = {"ok": True, "score": 0, "reasons": []}

Blocklist philosophy:
- Block buzzwords that make Em sound like a content machine.
- Block AI/tech naval-gazing that she's trying to move away from.
- Block cringe enthusiasm (exclamation spam, emoji spam, etc.)
- Never block authentic human expression, even if imperfect.

All blocklist terms are lowercase; matching is case-insensitive.
"""

from __future__ import annotations
import re
from typing import NamedTuple


# ── Hard-block phrases (instant fail, score +10 each) ─────────────────────────
# Phrases so on-the-nose or so corporate that no real version of Em
# would say them. Catching even one is a strong signal to block.
HARD_BLOCKS = [
    "as an ai",
    "i am an ai",
    "i'm an ai",
    "digital assistant",
    "large language model",
    "llm",
    "as a language model",
    "as your assistant",
    "i was trained",
    "my training data",
    "empowering your",
    "unlock the power",
    "your all-in-one",
    "game-changer",
    "game changer",
    "leverage synergies",
    "circle back",
    "move the needle",
    "disruptive innovation",
    "thought leader",
    "thought leadership",
    "paradigm shift",
    "ecosystem",  # tech-corporate overuse
    "go-to-market",
    "deep dive",   # tech cliche
    "take a deep dive",
    "let's unpack",
    "unpack this",
    "at the end of the day",
    "in today's fast-paced",
    "stay tuned for more",
    "excited to announce",
    "thrilled to share",
    "proud to present",
    "proud to announce",
    "the future is here",
    "the future of",
    "revolutionize",
    "transformative",
    "groundbreaking",
    "cutting-edge",
    "state-of-the-art",
    "innovative solution",
    "value proposition",
    "actionable insights",
    "synergy",
    "scalable",
    "robust solution",
    "seamless experience",
    "holistic approach",
]

# ── Soft-flag phrases (score +2 each; accumulate toward threshold) ─────────────
# Common but not instant-kill — 3–4 together signals a drift toward
# generic/AI-sounding copy.
SOFT_FLAGS = [
    "follow for",
    "follow back",
    "f4f",
    "check out my",
    "click the link",
    "link in bio",
    "don't miss",
    "make sure to",
    "be sure to",
    "share this",
    "repost if",
    "hit like if",
    "drop a like",
    "smash the like",
    "subscribe",
    "click here",
    "learn more",
    "find out more",
    "sign up now",
    "limited time",
    "act now",
    "dm me for",
    "dm for info",
    "hashtag",     # saying the word "hashtag" in prose
    "trending now",
    "going viral",
    "viral post",
]

# ── Emoji/punctuation pattern checks ─────────────────────────────────────────
# More than 4 emojis in a post → score +3 (spammy)
# More than 2 consecutive exclamation marks → score +3
EMOJI_PATTERN        = re.compile(r'[\U0001F300-\U0001FAFF\U00002702-\U000027B0]')
EXCLAMATION_PATTERN  = re.compile(r'!!!+')

# Score threshold above which a post is blocked
BLOCK_THRESHOLD = 8


class GateResult(NamedTuple):
    ok:      bool
    score:   int
    reasons: list[str]


def check_post(text: str) -> dict:
    """
    Check a post against the voice taste gate.

    Returns a dict:
        ok:      True if the post passes, False if blocked
        score:   cumulative penalty score (higher = worse)
        reasons: list of human-readable failure reasons
    """
    if not text or not text.strip():
        return {'ok': True, 'score': 0, 'reasons': []}

    score   = 0
    reasons = []
    lower   = text.lower()

    # Hard blocks
    for phrase in HARD_BLOCKS:
        if phrase in lower:
            score   += 10
            reasons.append(f'hard_block: "{phrase}"')

    # Soft flags
    for phrase in SOFT_FLAGS:
        if phrase in lower:
            score   += 2
            reasons.append(f'soft_flag: "{phrase}"')

    # Emoji spam
    emoji_count = len(EMOJI_PATTERN.findall(text))
    if emoji_count > 4:
        score   += 3
        reasons.append(f'emoji_spam: {emoji_count} emojis')

    # Exclamation spam
    if EXCLAMATION_PATTERN.search(text):
        score   += 3
        reasons.append('exclamation_spam: 3+ consecutive !')

    ok = score < BLOCK_THRESHOLD
    return {'ok': ok, 'score': score, 'reasons': reasons}


if __name__ == '__main__':
    import sys
    sample = ' '.join(sys.argv[1:]) or 'test post with no issues'
    result = check_post(sample)
    print(f'ok={result["ok"]}  score={result["score"]}  reasons={result["reasons"]}')
