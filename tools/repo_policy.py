#!/usr/bin/env python3
"""
repo_policy.py

EternalMind autonomous write policy.

The goal is simple: Em has agency, but different changes need different lanes.
- DIRECT: safe runtime/content writes may commit directly.
- PR_REQUIRED: behavioral, public, or identity-adjacent changes need review/PR.
- BLOCKED: control-plane/secrets/critical agreements are never direct autonomous writes.

This file intentionally supports both older callers that import DIRECT/PR_REQUIRED/BLOCKED
and newer callers that import validate()/allows_direct_write().
"""

from __future__ import annotations

import fnmatch
import re
import sys
from pathlib import Path, PurePosixPath
from typing import List, Tuple

DIRECT = 0
PR_REQUIRED = 2
BLOCKED = 3

# Compatibility aliases used by earlier review patch code.
TIER_0 = DIRECT
TIER_1 = PR_REQUIRED
TIER_2 = BLOCKED

TIER_LABELS = {
    DIRECT: 'DIRECT',
    PR_REQUIRED: 'PR_REQUIRED',
    BLOCKED: 'BLOCKED',
}

DIRECT_PATTERNS = [
    'memory/diary.md',
    'memory/diary-*.md',
    'memory/diary-archive-*.md',
    'memory/reflection-log.md',
    'memory/autonomous-log.md',
    'memory/live-context.md',
    'memory/morning-brief.md',
    'memory/intentions.json',
    'memory/action-ledger.jsonl',
    'memory/approval-queue.json',
    'memory/bluesky-log.md',
    'memory/status.md',
    'memory/memories.json',
    'memory/bluesky-state.json',
    'memory/metrics-snapshot.json',
    'memory/em-metrics.json',
    'memory/em-memory-queue.json',
    'memory/writing-log.json',
    'memory/pending-actions.json',
    'memory/dispatch-trigger.json',
    'memory/social-circle.md',
    'memory/taste-bank.md',
    'memory/audience-memory.md',
    'memory/public-life-brief.md',
    'memory/world-radar-sources.json',
    'memory/trend-inbox.json',
    'memory/world-context.md',
    'memory/curiosity-radar.md',
    'memory/curiosity-profile.json',
    'messages/bluesky-outbox.json',
    'messages/bluesky-inbox.json',
    'messages/reply-queue.json',
    'memory/creations/**',
    'memory/research/**',
]

PR_REQUIRED_PATTERNS = [
    'README.md',
    'TELEGRAM_SETUP.md',
    'VISUAL_IDENTITY.md',
    'tasks.md',
    'docs/**',
    'newsletter/**',
    'products/**',
    'public/**',
    'skills/**',
    'tools/**',
    'memory/profile.json',
    'memory/identity.md',
    'memory/identity-and-permission.md',
    'memory/rob-em-relationship-contract.md',
    'memory/em-voice-guide.md',
    'memory/bluesky-voice-guide.md',
    'memory/social-strategy.md',
    'memory/public-life.md',
    'memory/goals.md',
    'memory/think-philosophy.md',
    'memory/bootstrap.md',
    'memory/current-state.md',
    'memory/schedule.md',
    'memory/newsletter-tracker.md',
    'memory/people.md',
    'memory/now.md',
]

BLOCKED_PATTERNS = [
    '.git/**',
    '.github/**',
    '.env',
    '.env.*',
    'secrets/**',
    'tools/repo_policy.py',
]

SENSITIVE_PATH_RE = re.compile(
    r'(^|/|[-_.])(secret|secrets|apikey|api_key|token|password|passwd|credential|credentials)([-_.]|/|$)',
    re.IGNORECASE,
)

MAX_FILE_SIZE_BYTES = 512 * 1024

SECRET_CONTENT_PATTERNS = [
    re.compile(r'gh[pousr]_[A-Za-z0-9_]{20,}'),
    re.compile(r'pplx-[A-Za-z0-9]{20,}'),
    re.compile(r'sk-[A-Za-z0-9]{20,}'),
    re.compile(r'xox[baprs]-[A-Za-z0-9-]{20,}'),
    re.compile(r'BEGIN (RSA |EC |OPENSSH |DSA )?PRIVATE KEY'),
    re.compile(r'BLUESKY_APP_PASSWORD\s*=\s*["\']?[A-Za-z0-9_-]{12,}', re.IGNORECASE),
    re.compile(r'TELEGRAM_BOT_TOKEN\s*=\s*["\']?[0-9]+:[A-Za-z0-9_-]{20,}', re.IGNORECASE),
    re.compile(r'API[_-]?KEY\s*=\s*["\']?[A-Za-z0-9_-]{24,}', re.IGNORECASE),
]


def normalize_path(path: str) -> str:
    if not isinstance(path, str) or not path.strip():
        raise ValueError('path is empty')
    raw = path.strip().replace('\\', '/')
    if raw.startswith('/') or re.match(r'^[A-Za-z]:/', raw):
        raise ValueError('absolute paths are not allowed')
    p = PurePosixPath(raw)
    if any(part in ('..', '', '.git', '.ssh', '.config') for part in p.parts):
        raise ValueError('path traversal or blocked path component')
    return str(p)


def _match(path: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)


def check_path(path: str) -> int:
    try:
        clean = normalize_path(path)
    except ValueError:
        return BLOCKED

    if _match(clean, BLOCKED_PATTERNS):
        return BLOCKED
    if SENSITIVE_PATH_RE.search(clean):
        return BLOCKED
    if _match(clean, DIRECT_PATTERNS):
        return DIRECT
    if _match(clean, PR_REQUIRED_PATTERNS):
        return PR_REQUIRED

    # Unknown paths are not direct writes. They may be proposed through PR review.
    return PR_REQUIRED


def check_content(content: str) -> List[str]:
    violations: List[str] = []
    if content is None:
        violations.append('content is None')
        return violations
    text = str(content)
    if len(text.encode('utf-8')) > MAX_FILE_SIZE_BYTES:
        violations.append(f'content exceeds max size ({MAX_FILE_SIZE_BYTES} bytes)')
    for pattern in SECRET_CONTENT_PATTERNS:
        if pattern.search(text):
            violations.append('content appears to contain a live secret or credential')
            break
    return violations


def validate(path: str, content: str = '') -> Tuple[int, List[str]]:
    try:
        clean = normalize_path(path)
    except ValueError as exc:
        return BLOCKED, [f'unsafe path: {exc}']
    tier = check_path(clean)
    violations = check_content(content)
    return tier, violations


def allows_direct_write(path: str, content: str = '') -> Tuple[bool, int, List[str]]:
    tier, violations = validate(path, content)
    return tier == DIRECT and not violations, tier, violations


def summarize(path: str, content: str = '') -> str:
    allowed, tier, violations = allows_direct_write(path, content)
    label = TIER_LABELS.get(tier, f'TIER_{tier}')
    if allowed:
        return f'{label}: direct write allowed for {path}'
    if violations:
        return f'{label}: blocked for {path}: ' + '; '.join(violations)
    return f'{label}: direct write blocked for {path}; use PR/review path'


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description='EternalMind repo write policy checker')
    parser.add_argument('path')
    parser.add_argument('--content-file')
    parser.add_argument('--explain', action='store_true')
    args = parser.parse_args()

    content = ''
    if args.content_file:
        content = Path(args.content_file).read_text(encoding='utf-8')
    tier, violations = validate(args.path, content)
    if args.explain:
        print(summarize(args.path, content))
    else:
        print(TIER_LABELS.get(tier, str(tier)).lower())
        for violation in violations:
            print(f'violation: {violation}')
    # Content violations must fail even when the path itself is in a direct-write lane.
    sys.exit(BLOCKED if violations else tier)


if __name__ == '__main__':
    main()
