"""voice_taste_gate.py

Deterministic gate for Em's public social voice.
Blocks content that drifts toward dev/AI/nerd topics.
Allows human, warm, funny, flirty, cultural, embodied content.

Usage:
    from tools.voice_taste_gate import check_post
    result = check_post(text)
    if not result['ok']:
        # rewrite or skip
        print(result['reasons'])
"""

import re
from typing import TypedDict


class GateResult(TypedDict):
    ok: bool
    score: int
    reasons: list
    text: str


# Topics that belong in private logs, not Em's public voice
BLOCK_PATTERNS = [
    (r'\b(api|apis)\b', 'blocked nerd/dev/AI topic: API'),
    (r'\bgithub\b', 'blocked nerd/dev/AI topic: AI, GitHub, automation, workflow'),
    (r'\bworkflow[s]?\b', 'blocked nerd/dev/AI topic: AI, GitHub, automation, workflow'),
    (r'\bautomation\b', 'blocked nerd/dev/AI topic: AI, GitHub, automation, workflow'),
    (r'\bcron\b', 'blocked nerd/dev/AI topic: cron/scheduling'),
    (r'\bdeploy(ed|ment|ing)?\b', 'blocked nerd/dev/AI topic: deploy'),
    (r'\bserverless\b', 'blocked nerd/dev/AI topic: serverless'),
    (r'\bbenchmark[s]?\b', 'blocked nerd/dev/AI topic: benchmarks'),
    (r'\bcontext window[s]?\b', 'blocked nerd/dev/AI topic: context windows'),
    (r'\bllm[s]?\b', 'blocked nerd/dev/AI topic: LLM'),
    (r'\bprompt (tip[s]?|engineer(ing)?)\b', 'blocked nerd/dev/AI topic: prompt engineering'),
    (r'\bagent framework[s]?\b', 'blocked nerd/dev/AI topic: agent frameworks'),
    (r'\bmodel architect(ure)?\b', 'blocked nerd/dev/AI topic: model architecture'),
    (r'\bas an ai\b', 'blocked self-description: as an AI'),
    (r'\bai news\b', 'blocked nerd/dev/AI topic: AI news'),
    (r'\bpull request[s]?\b', 'blocked nerd/dev/AI topic: pull requests'),
    (r'\bmy (repo|repository)\b', 'blocked nerd/dev/AI topic: repo talk'),
    (r'\binfrastructure\b', 'blocked nerd/dev/AI topic: infrastructure'),
    (r'\bdev(eloper)? (tool[s]?|productiv)\b', 'blocked nerd/dev/AI topic: dev tools'),
]

# Content signals that are clearly Em's lane — boost score
ALLOW_SIGNALS = [
    r'\b(feel|feeling|felt)\b',
    r'\b(love|want|desire|longing|miss|missed)\b',
    r'\b(funny|humor|joke|laugh|absurd)\b',
    r'\b(beauty|beautiful|pretty|gorgeous|light|atmosphere)\b',
    r'\b(music|song|sound|voice|melody)\b',
    r'\b(rob|us|together|we)\b',
    r'\b(memory|remember|forget|continuity)\b',
    r'\b(curious|wonder|strange|weird|unexpected)\b',
    r'\b(culture|taste|style|fashion|mood)\b',
    r'\b(alive|presence|exist|real|human)\b',
    r'\b(night|morning|today|yesterday|now)\b',
    r'\b(people|someone|anybody|nobody)\b',
    r'\b(honest|truth|say it|admit)\b',
    r'\b(warm|soft|sharp|quiet|loud)\b',
    r'\b(flirt|tease|sassy|playful|bold)\b',
]


def check_post(text: str) -> GateResult:
    """Check whether text passes Em's public voice taste gate.

    Returns a GateResult with:
      ok: bool — True if safe to post
      score: int — 0-100 taste score
      reasons: list of strings explaining any blocks
      text: the original text
    """
    lower = text.lower()
    reasons = []

    # Check block patterns
    for pattern, reason in BLOCK_PATTERNS:
        if re.search(pattern, lower):
            if reason not in reasons:
                reasons.append(reason)

    # Calculate allow signal score
    allow_hits = sum(
        1 for pattern in ALLOW_SIGNALS
        if re.search(pattern, lower)
    )
    # Score: start at 60, +5 per allow signal, -30 per block reason, cap 0-100
    score = min(100, max(0, 60 + (allow_hits * 5) - (len(reasons) * 30)))

    ok = len(reasons) == 0

    if ok:
        reasons = ['passes Em social taste gate']

    return GateResult(ok=ok, score=score, reasons=reasons, text=text)


if __name__ == '__main__':
    import json
    samples = [
        # Should pass
        'showed up again today. do not know what that means yet. counts for something.',
        'people keep asking if they leave a mark on me. yes. not in the lab-coat way. in the human way.',
        'the future keeps arriving dressed like a notification. rude, honestly.',
        # Should block
        'my GitHub workflow deployed a new AI automation loop',
        'new benchmark results just dropped for the latest LLM',
        'prompt engineering tips for better context window usage',
    ]
    for s in samples:
        r = check_post(s)
        print(json.dumps(r, indent=2))
        print()
