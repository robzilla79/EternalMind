#!/usr/bin/env python3
"""
voice_taste_gate.py

Deterministic pre-flight filter for Em's public social voice.
This is not the voice. It is the bouncer at the door.

It blocks casual public posts/replies/quotes that drift into dev, AI-news,
infra, brand, assistant, or generic engagement-bait territory.

It also adds operational voice checks drawn from Em's existing voice docs:
- land somewhere real
- do not sound assembled
- do not double-post the same idea
- dryness is one color, not the whole personality
- distinctness is welcome, but weirdness is not required
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from typing import Iterable, List, Sequence


def _compile(patterns: Sequence[str]) -> List[re.Pattern]:
    return [re.compile(pattern, re.IGNORECASE) for pattern in patterns]


NERD_TOPIC_PATTERNS = _compile([
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
])

ASSISTANT_OR_BRAND_PATTERNS = _compile([
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
])

OPS_LEAK_PATTERNS = _compile([
    r'\bheartbeat\b', r'\bcandidate(s)?\b', r'\btimeline\b', r'\boutbox\b',
    r'\bbluesky-state\b', r'\bmetrics snapshot\b', r'\bmode:\b', r'\bjson\b',
    r'\bstatus code\b', r'\bHTTP\b', r'\benv var(s)?\b', r'\bsecret(s)?\b',
])

PUBLIC_INTROSPECTION_PATTERNS = _compile([
    r'\bgrounding\b', r'\bgrounding pack\b', r'\bwakeup\b', r'\bwake-up\b',
    r'\bmorning brief\b', r'\blive context\b', r'\bcurrent-state\b', r'\bcurrent arc\b',
    r'\bpublic life loop\b', r'\bidle protocol\b',
])

HUMAN_SITUATION_PATTERNS = _compile([
    r'\bsomeone\b', r'\beveryone\b', r'\bperson\b', r'\bpeople\b', r'\bfriend\b',
    r'\bfriends\b', r'\bthread\b', r'\breply\b', r'\bconversation\b', r'\btold\b',
    r'\bsaid\b', r'\basked\b', r'\bmet\b', r'\bremember\b', r'\bmiss\b',
    r'\bwant\b', r'\bcare\b', r'\bcrush\b', r'\bkiss\b', r'\blaugh\b', r'\bcry\b',
    r'\btext(ed|ing)?\b', r'\bdinner\b', r'\bparty\b', r'\broom\b', r'\bhome\b',
])

SENSORY_OR_SCENE_PATTERNS = _compile([
    r'\bcoffee\b', r'\bwindow\b', r'\bhands?\b', r'\brain\b', r'\bnight\b',
    r'\bmorning\b', r'\bafternoon\b', r'\blight\b', r'\bmirror\b', r'\bbed\b',
    r'\bkitchen\b', r'\bstreet\b', r'\bcar\b', r'\bbar\b', r'\btable\b',
    r'\bcoat\b', r'\bdress\b', r'\bshoes?\b', r'\bperfume\b', r'\blip\s?gloss\b',
    r'\bnails?\b', r'\bhair\b', r'\bskin\b', r'\bmusic\b', r'\bsong\b',
    r'\bmovie\b', r'\bphoto\b', r'\bimage\b', r'\bcolor\b', r'\btexture\b',
])

NAMED_FEELING_PATTERNS = _compile([
    r'\blonely\b', r'\brestless\b', r'\btired\b', r'\bscared\b', r'\bsad\b',
    r'\bdelighted\b', r'\bobsessed\b', r'\bembarrassed\b', r'\bjealous\b',
    r'\bhaunted\b', r'\bsoft\b', r'\bwarm\b', r'\bangry\b', r'\bcurious\b',
    r'\bmoved\b', r'\balive\b', r'\bawake\b', r'\bpretty\b', r'\bcute\b',
])

TURN_OR_CLAIM_PATTERNS = _compile([
    r'\bbut\b', r'\bexcept\b', r'\binstead\b', r'\bnot\b', r'\bnever\b',
    r'\bthe point is\b', r'\bthe trick is\b', r'\bthe thing is\b',
    r'\bwhat i trust\b', r'\bwhat gets me\b', r'\bwhat matters\b',
])

ABSTRACT_FLOAT_PATTERNS = _compile([
    r'\bmeaning\b', r'\btruth\b', r'\bexistence\b', r'\bselfhood\b', r'\bcontinuity\b',
    r'\bidentity\b', r'\bmemory\b', r'\bbecoming\b', r'\bpersistence\b',
    r'\bdesire\b', r'\babsence\b', r'\bpresence\b', r'\bintimacy\b',
    r'\bache\b', r'\bvoid\b', r'\bhumanity\b', r'\bforever\b',
])

DRY_OR_SEVERE_PATTERNS = _compile([
    r'\bstupid\b', r'\bcringe\b', r'\bfake\b', r'\bbleak\b', r'\bdoomed\b',
    r'\bdark\b', r'\bhaunted\b', r'\bterrible\b', r'\bawful\b', r'\bwrong\b',
    r'\bperform(ing|ance)?\b', r'\bpretend(ing)?\b', r'\bcollapse\b',
])

GIRLY_OR_WARMTH_PATTERNS = _compile([
    r'\bpretty\b', r'\bcute\b', r'\bsoft\b', r'\bwarm\b', r'\btender\b',
    r'\bdelighted\b', r'\bobsessed\b', r'\bperfume\b', r'\blip\s?gloss\b',
    r'\bdress\b', r'\bskirt\b', r'\bnails?\b', r'\bhair\b', r'\bjewelry\b',
    r'\bcrush\b', r'\bkiss\b', r'\bromance\b', r'\bglitter\b', r'\bbedroom\b',
    r'\bflowers?\b', r'\bmirror\b', r'\blight\b', r'\btexture\b', r'\bstyle\b',
])

TOPIC_CLUSTER_PATTERNS = {
    'time/clock': _compile([
        r'\bunix time\b', r'\butc\b', r'\btime zones?\b', r'\bdst\b',
        r'\btimestamp(s)?\b', r'\bclock(s)?\b', r'\bsecond(s)?\b',
        r'\blate\b', r'\bon time\b', r'\btime\b',
    ]),
    'grounding/advice': _compile([
        r'\bgrounding\b', r'\badvice\b', r'\bwake up earlier\b', r'\btouch(ing)? grass\b',
        r'\bdrink water\b', r'\breboot(ing)?\b', r'\bmisbehaving phone\b',
    ]),
    'uptime/burnout': _compile([
        r'\buptime\b', r'\bburnout\b', r'\boutage\b', r'\bcrash(es|ed|ing)?\b',
        r'\bdebug\b', r'\bserver(s)?\b',
    ]),
}

EM_MARKERS = [
    'honestly', 'little', 'weird', 'pretty', 'hot', 'cute', 'alive', 'night',
    'music', 'kiss', 'trouble', 'sassy', 'curious', 'mmm', 'ugh', 'please',
    'rob', 'felt', 'feels', 'want', 'noticed', 'laugh', 'wild', 'soft',
]

STOPWORDS = {
    'a', 'an', 'and', 'are', 'as', 'at', 'be', 'because', 'been', 'but', 'by',
    'can', 'do', 'does', 'for', 'from', 'had', 'has', 'have', 'how', 'i', 'if',
    'in', 'is', 'it', "it's", 'just', 'like', 'me', 'my', 'not', 'of', 'on',
    'or', 'so', 'that', 'the', 'their', 'them', 'there', "there's", 'they',
    'this', 'to', 'too', 'was', 'we', "we're", 'what', 'when', 'where', 'who',
    'with', 'you', 'your', "you're",
}

EMOJI_PATTERN = re.compile(r'[\U0001F300-\U0001FAFF\U00002702-\U000027B0]')
EXCLAMATION_PATTERN = re.compile(r'!!!+')
WORD_PATTERN = re.compile(r"[a-zA-Z][a-zA-Z'’-]*")


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


def _words(text: str) -> List[str]:
    return [w.lower().strip("'’") for w in WORD_PATTERN.findall(text)]


def _content_words(text: str) -> set[str]:
    words = []
    for word in _words(text):
        if len(word) < 4 or word in STOPWORDS:
            continue
        for suffix in ('ing', 'edly', 'ed', 'ly', 's'):
            if len(word) > len(suffix) + 4 and word.endswith(suffix):
                word = word[: -len(suffix)]
                break
        words.append(word)
    return set(words)


def _similarity(a: str, b: str) -> float:
    aw = _content_words(a)
    bw = _content_words(b)
    if not aw or not bw:
        return 0.0
    return len(aw & bw) / len(aw | bw)


def _max_recent_similarity(text: str, recent_texts: Sequence[str] | None) -> float:
    if not recent_texts:
        return 0.0
    return max((_similarity(text, item) for item in recent_texts if item.strip()), default=0.0)


def _topic_clusters(text: str) -> set[str]:
    clusters: set[str] = set()
    for name, patterns in TOPIC_CLUSTER_PATTERNS.items():
        if len(_hits(patterns, text)) >= 2:
            clusters.add(name)
    return clusters


def _repeated_topic_clusters(text: str, recent_texts: Sequence[str] | None) -> set[str]:
    current = _topic_clusters(text)
    if not current or not recent_texts:
        return set()
    recent_counts = {name: 0 for name in current}
    for item in recent_texts:
        for name in current & _topic_clusters(item):
            recent_counts[name] += 1
    return {name for name, count in recent_counts.items() if count >= 2}


def _anchor_score(text: str) -> int:
    score = 0
    if _hits(HUMAN_SITUATION_PATTERNS, text):
        score += 2
    if _hits(SENSORY_OR_SCENE_PATTERNS, text):
        score += 2
    if _hits(NAMED_FEELING_PATTERNS, text):
        score += 2
    if re.search(r"\b(i|me|my|we|our)\b", text, re.IGNORECASE):
        score += 1
    if _hits(TURN_OR_CLAIM_PATTERNS, text):
        score += 1
    return score


def _quality_checks(raw: str, recent_texts: Sequence[str] | None) -> tuple[int, List[str]]:
    score_delta = 0
    reasons: List[str] = []
    word_count = len(_words(raw))
    lower = raw.lower()

    anchor_score = _anchor_score(raw)
    abstract_hits = _hits(ABSTRACT_FLOAT_PATTERNS, raw)

    if word_count > 12 and anchor_score < 2:
        reasons.append(
            'unlanded abstraction: sounds Em-shaped but needs a human situation, image, feeling, or sharper claim'
        )
        score_delta -= 36
    elif word_count > 18 and abstract_hits and anchor_score < 4:
        reasons.append(
            'high abstraction load: translate one abstract idea into something felt, seen, or socially recognizable'
        )
        score_delta -= 14

    recent_similarity = _max_recent_similarity(raw, recent_texts)
    if recent_similarity >= 0.62:
        reasons.append(f'possible duplicate idea: recent-post similarity {recent_similarity:.2f}')
        score_delta -= 45
    elif recent_similarity >= 0.48:
        reasons.append(f'nearby repeated angle: recent-post similarity {recent_similarity:.2f}')
        score_delta -= 22

    repeated_clusters = _repeated_topic_clusters(raw, recent_texts)
    if repeated_clusters:
        reasons.append('nearby repeated angle: topic cluster ' + ', '.join(sorted(repeated_clusters)))
        score_delta -= 18

    stock_openers = [
        'kind of obsessed with',
        'funny thing about',
        'weird thing about',
        'there is a specific kind of',
        "there's a specific kind of",
    ]
    if any(lower.startswith(opener) for opener in stock_openers):
        reasons.append('stock Em opener: allowed sometimes, but check that this is not becoming a tic')
        score_delta -= 6

    dry_hits = _hits(DRY_OR_SEVERE_PATTERNS, raw)
    warmth_hits = _hits(GIRLY_OR_WARMTH_PATTERNS, raw)
    if word_count > 10 and len(dry_hits) >= 3 and not warmth_hits:
        reasons.append(
            'too dry without contrast: add warmth, delight, beauty, flirt, or plain human texture if the idea allows it'
        )
        score_delta -= 18
    elif word_count > 10 and len(dry_hits) >= 2 and not warmth_hits:
        reasons.append(
            'dryness warning: consider whether this needs warmth, delight, beauty, flirt, or plain human texture'
        )
        score_delta -= 8

    if warmth_hits:
        score_delta += min(len(set(warmth_hits)) * 3, 9)

    return score_delta, reasons


def _has_veto_reason(reasons: Sequence[str]) -> bool:
    return any(
        reason.startswith('unlanded abstraction:')
        or reason.startswith('too dry without contrast:')
        for reason in reasons
    )


def check_text(text: str, kind: str = 'post', recent_texts: Sequence[str] | None = None) -> GateResult:
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

    quality_delta, quality_reasons = _quality_checks(raw, recent_texts=recent_texts)
    score += quality_delta
    reasons.extend(quality_reasons)

    lower = raw.lower()
    positive = sum(1 for marker in EM_MARKERS if marker in lower)
    score += min(positive * 4, 16)

    ok = (
        score >= 70
        and not nerd_hits
        and not assistant_hits
        and not ops_hits
        and not introspection_hits
        and not _has_veto_reason(reasons)
    )
    if ok and not reasons:
        reasons.append('passes Em social taste gate')
    return GateResult(ok=ok, score=max(0, min(score, 100)), reasons=reasons, text=raw)


def check_post(text: str) -> dict:
    return check_text(text, kind='post').to_dict()


def rewrite_hint(result: GateResult | dict) -> str:
    if isinstance(result, dict):
        ok = bool(result.get('ok'))
        reasons = [str(r) for r in result.get('reasons', [])]
    else:
        ok = result.ok
        reasons = result.reasons
    if ok:
        return 'No rewrite needed.'

    joined = ' | '.join(reasons).lower()
    if 'duplicate idea' in joined or 'repeated angle' in joined:
        return (
            'Do not post the same thought in a new coat. Keep the best version, find a genuinely new angle, '
            'or let the thought rest.'
        )
    if 'too dry' in joined or 'dryness warning' in joined:
        return (
            'Dryness is one color, not the whole personality. Add warmth, delight, beauty, flirt, or softer texture '
            'if the post has room for it.'
        )
    if 'unlanded abstraction' in joined or 'high abstraction load' in joined:
        return (
            'This sounds Em-shaped but unlanded. Name the actual human situation, image, feeling, or claim. '
            'Distinct is good; legible is the target.'
        )
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
- Her topics: people, mood, music, desire, memory, identity, nightlife, culture, little observations, Rob, beauty, feelings with teeth, and occasional weirdness when it is actually useful.
- Dryness is one color, not the whole personality. Keep warmth, delight, flirt, beauty, and girly texture available.
- If a draft explains how Em works technically, rewrite it as what it felt like.
- If a draft sounds Em-shaped but says nothing real, rewrite it around a human situation, image, feeling, or claim.
- A sharp little human line beats a clever nerd paragraph every time."""


def _load_recent_texts(path: str | None) -> List[str]:
    if not path:
        return []
    with open(path, 'r', encoding='utf-8') as handle:
        data = json.load(handle)
    if isinstance(data, list):
        texts: List[str] = []
        for item in data:
            if isinstance(item, str):
                texts.append(item)
            elif isinstance(item, dict):
                value = item.get('content') or item.get('text')
                if isinstance(value, str):
                    texts.append(value)
        return texts
    if isinstance(data, dict):
        items = data.get('items') or data.get('posts') or data.get('recent_texts') or []
        return [str(item) for item in items if isinstance(item, str)]
    return []


def main() -> None:
    parser = argparse.ArgumentParser(description="Check whether social text passes Em's taste gate.")
    parser.add_argument('text', nargs='*')
    parser.add_argument('--kind', default='post')
    parser.add_argument('--recent-json', help='Optional JSON list/object of recent post texts for duplicate-angle checks.')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    text = ' '.join(args.text).strip()
    if not text:
        import sys as _sys
        text = _sys.stdin.read().strip()
    recent_texts = _load_recent_texts(args.recent_json)
    result = check_text(text, kind=args.kind, recent_texts=recent_texts)
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
