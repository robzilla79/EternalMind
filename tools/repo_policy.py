#!/usr/bin/env python3
"""
repo_policy.py

EternalMind write policy engine.
Every autonomous file write should be validated here before committing.

Three risk tiers:

  TIER_0 — Direct commit allowed (content/state updates)
  TIER_1 — PR required, auto-merge allowed after checks (behavioral files)
  TIER_2 — PR required, NO autonomous merge (control plane)

Usage:
    from repo_policy import check_path, TIER_0, TIER_1, TIER_2
    tier = check_path("memory/diary.md")      # returns 0
    tier = check_path("tools/bluesky_sync.py") # returns 1
    tier = check_path(".github/workflows/x.yml") # returns 2
"""
import re
from pathlib import PurePosixPath

TIER_0 = 0  # direct commit
TIER_1 = 1  # PR, auto-merge ok
TIER_2 = 2  # PR, no autonomous merge

# Order matters — first match wins
_RULES = [
    # TIER 2 — control plane (check first, most restrictive)
    (TIER_2, re.compile(r'^\.github/')),
    (TIER_2, re.compile(r'^secrets/')),
    (TIER_2, re.compile(r'^\.env')),
    (TIER_2, re.compile(r'^requirements\.txt$')),
    (TIER_2, re.compile(r'^pyproject\.toml$')),
    (TIER_2, re.compile(r'^package\.json$')),

    # TIER 1 — behavioral
    (TIER_1, re.compile(r'^tools/')),
    (TIER_1, re.compile(r'^skills/')),
    (TIER_1, re.compile(r'^public/assets/')),
    (TIER_1, re.compile(r'^memory/.*\.json$')),
    (TIER_1, re.compile(r'^products/')),

    # TIER 0 — safe content/state (default for memory/, messages/, public/)
    (TIER_0, re.compile(r'^memory/')),
    (TIER_0, re.compile(r'^messages/')),
    (TIER_0, re.compile(r'^public/')),
]

_DEFAULT_TIER = TIER_1  # unknown paths get tier 1 — PR but auto-mergeable

MAX_FILE_SIZE_BYTES = 512 * 1024  # 512KB hard limit on autonomous writes

_BLOCKED_PATTERNS = [
    re.compile(r'GITHUB_TOKEN\s*=\s*["\']?[a-zA-Z0-9_-]{20,}'),
    re.compile(r'PERPLEXITY_API_KEY\s*=\s*["\']?pplx-[a-zA-Z0-9]+'),
    re.compile(r'password\s*=\s*["\']?.{8,}', re.IGNORECASE),
]


def check_path(path: str) -> int:
    """Return the risk tier for a given repo path."""
    p = str(PurePosixPath(path))
    for tier, pattern in _RULES:
        if pattern.match(p):
            return tier
    return _DEFAULT_TIER


def check_content(content: str) -> list:
    """
    Scan content for blocked patterns (secrets, credentials).
    Returns list of violation strings. Empty list = clean.
    """
    violations = []
    for pattern in _BLOCKED_PATTERNS:
        if pattern.search(content):
            violations.append(f"Blocked pattern matched: {pattern.pattern[:40]}...")
    if len(content.encode()) > MAX_FILE_SIZE_BYTES:
        violations.append(f"Content exceeds max size ({MAX_FILE_SIZE_BYTES} bytes)")
    return violations


def validate(path: str, content: str) -> tuple:
    """
    Full validation. Returns (tier, violations).
    violations is a list of strings — empty means safe to proceed.
    """
    tier = check_path(path)
    violations = check_content(content)
    return tier, violations


if __name__ == "__main__":
    # Quick self-test
    test_cases = [
        "memory/diary.md",
        "memory/memories.json",
        "tools/bluesky_sync.py",
        ".github/workflows/em-dispatch.yml",
        "public/index.html",
        "products/my-product.md",
        "requirements.txt",
    ]
    labels = ["DIRECT", "PR+AUTO", "PR+HOLD"]
    for p in test_cases:
        t = check_path(p)
        print(f"  {labels[t]:10s}  {p}")
