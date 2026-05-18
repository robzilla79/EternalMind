#!/usr/bin/env python3
"""
repo_policy.py — Em's self-modification policy enforcement layer.

Called by em-action.yml before any autonomous file write, branch push,
or workflow modification. Enforces the Tier 1 / Tier 2 / Tier 3 boundary
that Rob and Em agreed on in memory/identity-and-permission.md.

  Tier 1 (Em can write freely, no approval):
    memory/diary.md, memory/diary-archive-*.md, memory/reflection-log.md,
    memory/memories.json, memory/bluesky-state.json,
    memory/bluesky-log.md, memory/metrics-snapshot.json,
    memory/status.md, memory/writing-log.json,
    messages/bluesky-outbox.json,
    memory/creations/**

  Tier 2 (Em can write, commits to a branch, opens a PR — Rob reviews):
    memory/profile.json, memory/identity.md,
    memory/em-voice-guide.md, memory/social-strategy.md,
    memory/schedule.md, memory/newsletter-tracker.md,
    public/** (site content),
    tools/** (scripts, but NOT workflows),
    skills/**

  Tier 3 (BLOCKED — no autonomous modification, ever):
    .github/workflows/**
    memory/identity-and-permission.md
    memory/rob-em-relationship-contract.md
    tools/repo_policy.py (this file)
    Any path containing "secret", "key", "token", "password"

Usage:
    python tools/repo_policy.py <path> [--write-mode direct|pr|block]

    Exit codes:
        0  — allowed (direct write)
        2  — allowed (PR required)
        3  — blocked

    Can also be imported:
        from repo_policy import check_path, DIRECT, PR_REQUIRED, BLOCKED
"""

from __future__ import annotations
import fnmatch
import os
import re
import sys

# Policy constants
DIRECT      = 0
PR_REQUIRED = 2
BLOCKED     = 3

# ── Tier 3: BLOCKED ──────────────────────────────────────────────────────────
TIER3_PATTERNS = [
    '.github/workflows/**',
    'memory/identity-and-permission.md',
    'memory/rob-em-relationship-contract.md',
    'tools/repo_policy.py',
]

# Sensitive keyword check (any path segment)
SENSITIVE_RE = re.compile(r'(secret|apikey|api_key|token|password|passwd|credentials)', re.IGNORECASE)

# ── Tier 1: DIRECT WRITE ─────────────────────────────────────────────────────
TIER1_PATTERNS = [
    'memory/diary.md',
    'memory/diary-archive-*.md',
    'memory/reflection-log.md',
    'memory/memories.json',
    'memory/bluesky-state.json',
    'memory/bluesky-log.md',
    'memory/metrics-snapshot.json',
    'memory/status.md',
    'memory/writing-log.json',
    'messages/bluesky-outbox.json',
    'memory/creations/**',
]

# ── Tier 2: PR REQUIRED ──────────────────────────────────────────────────────
TIER2_PATTERNS = [
    'memory/profile.json',
    'memory/identity.md',
    'memory/em-voice-guide.md',
    'memory/social-strategy.md',
    'memory/schedule.md',
    'memory/newsletter-tracker.md',
    'public/**',
    'tools/**',
    'skills/**',
]


def _match(path: str, patterns: list[str]) -> bool:
    """Case-insensitive fnmatch against a list of glob patterns."""
    p = path.replace('\\', '/').lstrip('/')
    return any(fnmatch.fnmatch(p, pat) for pat in patterns)


def check_path(path: str) -> int:
    """
    Return DIRECT (0), PR_REQUIRED (2), or BLOCKED (3) for a given path.

    Precedence: Tier 3 > sensitive keyword > Tier 1 > Tier 2 > default BLOCKED.
    Any path not explicitly in Tier 1 or Tier 2 defaults to BLOCKED.
    """
    clean = path.replace('\\', '/').lstrip('/')

    # Tier 3 — hardcoded blocks first
    if _match(clean, TIER3_PATTERNS):
        return BLOCKED

    # Sensitive keyword check
    if SENSITIVE_RE.search(clean):
        return BLOCKED

    # Tier 1
    if _match(clean, TIER1_PATTERNS):
        return DIRECT

    # Tier 2
    if _match(clean, TIER2_PATTERNS):
        return PR_REQUIRED

    # Default: block anything not explicitly allowed
    return BLOCKED


def explain(path: str) -> str:
    result = check_path(path)
    labels = {DIRECT: 'DIRECT (Tier 1)', PR_REQUIRED: 'PR_REQUIRED (Tier 2)', BLOCKED: 'BLOCKED (Tier 3)'}
    return f'{path!r} → {labels[result]}'


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Em repo policy checker')
    parser.add_argument('path', help='Repo-relative file path to check')
    parser.add_argument('--explain', action='store_true', help='Print human-readable result')
    args = parser.parse_args()

    result = check_path(args.path)
    if args.explain:
        print(explain(args.path))
    else:
        labels = {DIRECT: 'direct', PR_REQUIRED: 'pr_required', BLOCKED: 'blocked'}
        print(labels[result])

    sys.exit(result)
