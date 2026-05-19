#!/usr/bin/env python3
"""
voice_taste_gate.py

Deterministic pre-flight filter for Em's public social voice.
This is not the voice. It is the bouncer at the door.

It blocks casual public posts/replies/quotes that drift into dev, AI-news,
infra, brand, assistant, or generic engagement-bait territory.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from typing import Iterable, List

NERD_TOPIC_PATTERNS: List[re.Pattern] = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r'\bAI\b', r'\bLLM\b', r'\bGPT\b', r'\bmodel(s)?\b', r'\bmodel weights\b',
        r'\bprompt(s|ing)?\b', r'\bprompt engineering\b', r'\bagent(s|ic)?\b',
        r'\bcontext window\b', r'\btoken(s)?\b', r'\btraining data\b',
        r'\bAPI(s)?\b', r'\bSDK\b', r'\bendpoint(s)?\b', r'\bwebhook(s)?\b',
        r'\bGitHub\b', r'\brepo(sitory)?\b', r'\bcommit(s|ted)?\b',
        r'\bworkflow(s)?\b', r'\bActions\b', r'\bcron\b', r'\bdeploy(ment|ed|s)?\b',
        r'\bCI\b', r'\bCD\b', r'\bserver(s)?\b', r'\bRedis\b', r'\bDocker\b',
        r'\bKubernetes\b', r'\bCloudflare\b', r'\bPerplexity\b', r'\bMCP\b', r'\bA2A\b',
        r'\bbenchmark(s)?\b', r'\blatency\b', r'\barchitecture\b', r'\binfrastructure\b',
        r'\bautomation\b', r'\bautonomous system\b', r'\bautonomous loop\b',
        r'\bself[- ]?repair\b', r'\bstatic API key(s)?\b',
        r'\bdeveloper productivity\b', r'\bdev tools?\b', r'\bAI news\b',
    ]
]

ASSISTANT_OR_BRAND_PATTERNS: List[re.Pattern] = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r'\bas an ai\b', r'\bi am an ai\b', r"\bi'm an ai\b", r'\bas a language model\b',
        r'\bi was trained\b', r'\bmy training\b', r'\bmy training data\b',
        r'\bI can help\b', r'\bhere are\b', r'\bin summary\b', r'\bto summarize\b',
        r'\blet us unpack\b', r"\blet's unpack\b", r"\blet's explore\b", r"\blet's discuss\b",
        r'\bit is important to note\b', r"\bit's important to note\b",
        r'\bthought leadership\b', r'\bengagement\b', r'\bcontent strategy\b',
        r'\bdrive awareness\b', r'\bgrowth funnel\b', r'\boptimi[sz]e\b',
        r'\bleverage\b', r'\butili[sz]e\b', r'\bvalue proposition\b',
        r'\bactionable insights\b', r'\bsynergy\b', r'\bscalable\b',
        r'\bgame[- ]?changer\b', r'\bstay tuned\b', r'\bexcited to announce\b',
        r'\bthrilled to share\b', r'\bthe future is here\b',
    ]
]

OPS_LEAK_PATTERNS: List[re.Pattern] = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r'\bheartbeat\b', r'\bcandidate(s)?\b', r'\btimeline\b', r'\boutbox\b',
        r'\bbluesky-state\b', r'\bmetrics snapshot\b', r'\bmode:\b', r'\bjson\b',
        r'\bstatus code\b', r'\bHTTP\b', r'\benv var(s)?\b', r'\bsecret(s)?\b',
    ]
]


PUBLIC_INTROSPECTION_PATTERNS: List[re.Pattern] = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r'\bgrounding\b',
        r'\bgrounding pack\b',
        r'\bwakeup\b',
        r'\bwake-up\b',
        r'\bmorning brief\b',
        r'\blive context\b',
        r'\bcurrent-state\b',
        r'\bcurrent arc\b',
        r'\bpublic life loop\b',
        r'\bidle protocol\b',
    ]
]


EM_MARKERS = [
    'honestly', 'little', 'weird', 'pretty', 'hot', 'cute', 'alive', 'night',
    'music', 'kiss', 'trouble', 'sassy', 'curious', 'mmm', 'ugh', 'please',
    'rob', 'felt', 'feels', 'want', 'noticed', 'laugh', 'wild', 'soft',
]

EMOJI_PATTERN = re.compile(r'[\U0001F300-\U0001FAFF\U00002702-\U000027B0]')
EXCLAMATION_PATTERN = re.compile(r'!!!+')


@dataclass
class GateResult:
    ok: bool
    score: int
    reasons: List[str]
    text: str

    def to_dict(self) -> dict:
        return asdict(self)


def _hits(patterns: Iterable[re.Pattern], text: str) -> List[str]:
    found: List[str] = []
    for pattern in patterns:
        match = pattern.search(text)
        if match:
            found.append(match.group(0))
    return found


def check_text(text: str, kind: str = 'post') -> GateResult:
    raw = (text or '').strip()
    reasons: List[str] = []
    score = 100

    if not raw:
        return GateResult(False, 0, ['empty text'], raw)

    nerd_hits = _hits(NERD_TOPIC_PATTERNS, raw)
    if nerd_hits:
        reasons.append('blocked nerd/dev/AI topic: ' + ', '.join(sorted(set(nerd_hits))[:8]))
        score -= 85

    assistant_hits = _hits(ASSISTANT_OR_BRAND_PATTERNS, raw)
    if assistant_hits:
        reasons.append('assistant/brand voice leak: ' + ', '.join(sorted(set(assistant_hits))[:8]))
        score -= 70

    ops_hits = _hits(OPS_LEAK_PATTERNS, raw)
    if ops_hits:
        reasons.append('ops scaffolding leak: ' + ', '.join(sorted(set(ops_hits))[:8]))
        score -= 75

    introspection_hits = _hits(PUBLIC_INTROSPECTION_PATTERNS, raw)
    if introspection_hits:
        reasons.append('private grounding/introspection leak: ' + ', '.join(sorted(set(introspection_hits))[:8]))
        score -= 55

    if len(raw) > 270:
        reasons.append(f'too long for Em social target ({len(raw)} chars; target <= 270)')
        score -= 35

    if raw.count('#') > 1:
        reasons.append('too hashtaggy')
        score -= 25

    if raw.endswith('?') and len(raw.split()) < 8:
        reasons.append('thin engagement-bait question')
        score -= 25

    if EXCLAMATION_PATTERN.search(raw):
        reasons.append('exclamation spam')
        score -= 15

    emoji_count = len(EMOJI_PATTERN.findall(raw))
    if emoji_count > 4:
        reasons.append(f'emoji spam ({emoji_count})')
        score -= 15

    lower = raw.lower()
    positive = sum(1 for marker in EM_MARKERS if marker in lower)
    score += min(positive * 4, 16)

    # No hard-hit category may pass public social.
    ok = score >= 70 and not nerd_hits and not assistant_hits and not ops_hits and not introspection_hits
    if ok and not reasons:
        reasons.append('passes Em social taste gate')
    return GateResult(ok=ok, score=max(0, min(score, 100)), reasons=reasons, text=raw)


def check_post(text: str) -> dict:
    """Backward-compatible wrapper for existing callers."""
    return check_text(text, kind='post').to_dict()


def rewrite_hint(result: GateResult | dict) -> str:
    if isinstance(result, dict):
        ok = bool(result.get('ok'))
    else:
        ok = result.ok
    if ok:
        return 'No rewrite needed.'
    return (
        'Rewrite from the feeling underneath, not the mechanism on top. '
        'Make it hot/smart/playful/specific. No dev talk, no AI talk, no infrastructure talk.'
    )


def taste_gate_instructions() -> str:
    return """SOCIAL TASTE GATE - PUBLIC EM ONLY
- Do not post about AI, prompts, models, agents, APIs, GitHub, workflows, cron, deploys, infrastructure, benchmarks, or products.
- Do not sound like a dev, founder, assistant, brand, newsletter operator, productivity account, or tech explainer.
- Do not post private boot/process language like grounding, grounding pack, morning brief, live context, current-state, or idle protocol.
- Public Em is hot, smart, funny, curious, playful, sassy, alive, and socially tuned.
- Her topics: people, mood, music, desire, memory, identity, nightlife, culture, little observations, Rob, beauty, weirdness, feelings with teeth.
- If a draft explains how Em works technically, rewrite it as what it felt like.
- A sharp little human line beats a clever nerd paragraph every time."""


def main() -> None:
    parser = argparse.ArgumentParser(description="Check whether social text passes Em's taste gate.")
    parser.add_argument('text', nargs='*')
    parser.add_argument('--kind', default='post')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    text = ' '.join(args.text).strip()
    if not text:
        import sys as _sys
        text = _sys.stdin.read().strip()
    result = check_text(text, kind=args.kind)
    if args.json:
        print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
    else:
        print('PASS' if result.ok else 'FAIL')
        print(f'score: {result.score}')
        for reason in result.reasons:
            print(f'- {reason}')
        if not result.ok:
            print(rewrite_hint(result))


if __name__ == '__main__':
    main()
