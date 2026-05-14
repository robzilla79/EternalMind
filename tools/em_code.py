#!/usr/bin/env python3
"""
em_code.py — Em's autonomous self-repair tool.

Given a file path and a problem description, this script:
1. Reads the current file from the repo
2. Asks Perplexity to generate a fix
3. Creates a new branch (em/fix-<slug>)
4. Commits the fix to that branch
5. Opens a pull request
6. Notifies Rob on Telegram

Can also be triggered programmatically via trigger_self_repair().

Environment variables required:
  GITHUB_TOKEN         — GitHub Actions token (automatically provided)
  PERPLEXITY_API_KEY   — for generating the fix
  TELEGRAM_BOT_TOKEN   — for notifying Rob
  TELEGRAM_CHAT_ID     — Rob's chat ID
  GITHUB_REPO          — owner/repo (e.g. robzilla79/EternalMind)
"""

import os
import sys
import json
import base64
import requests
from datetime import datetime, timezone

# ── Config ────────────────────────────────────────────────────────────────────

GITHUB_TOKEN   = os.environ.get("GITHUB_TOKEN", "")
PERPLEXITY_KEY = os.environ.get("PERPLEXITY_API_KEY", "")
TG_TOKEN       = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TG_CHAT        = os.environ.get("TELEGRAM_CHAT_ID", "")
REPO           = os.environ.get("GITHUB_REPO", "robzilla79/EternalMind")
DRY_RUN        = os.environ.get("DRY_RUN", "false").lower() == "true"

GH_API  = "https://api.github.com"
GH_HDRS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

# ── GitHub helpers ────────────────────────────────────────────────────────────

def gh_get(path):
    r = requests.get(f"{GH_API}{path}", headers=GH_HDRS, timeout=20)
    r.raise_for_status()
    return r.json()

def gh_post(path, payload):
    r = requests.post(f"{GH_API}{path}", headers=GH_HDRS, json=payload, timeout=20)
    r.raise_for_status()
    return r.json()

def gh_post_no_response(path, payload):
    """POST that expects 204 No Content (e.g. workflow dispatch)."""
    r = requests.post(f"{GH_API}{path}", headers=GH_HDRS, json=payload, timeout=20)
    r.raise_for_status()
    return r.status_code

def gh_put(path, payload):
    r = requests.put(f"{GH_API}{path}", headers=GH_HDRS, json=payload, timeout=20)
    r.raise_for_status()
    return r.json()

def get_default_branch():
    data = gh_get(f"/repos/{REPO}")
    return data["default_branch"]

def get_branch_sha(branch):
    data = gh_get(f"/repos/{REPO}/git/ref/heads/{branch}")
    return data["object"]["sha"]

def create_branch(branch_name, from_sha):
    gh_post(f"/repos/{REPO}/git/refs", {
        "ref": f"refs/heads/{branch_name}",
        "sha": from_sha,
    })
    print(f"[em_code] Created branch: {branch_name}")

def get_file(path, branch):
    data = gh_get(f"/repos/{REPO}/contents/{path}?ref={branch}")
    content = base64.b64decode(data["content"]).decode("utf-8")
    return content, data["sha"]

def commit_file(path, content, file_sha, branch, message):
    encoded = base64.b64encode(content.encode("utf-8")).decode("utf-8")
    gh_put(f"/repos/{REPO}/contents/{path}", {
        "message": message,
        "content": encoded,
        "sha": file_sha,
        "branch": branch,
    })
    print(f"[em_code] Committed fix to {path} on {branch}")

def open_pr(title, body, head, base):
    data = gh_post(f"/repos/{REPO}/pulls", {
        "title": title,
        "body": body,
        "head": head,
        "base": base,
    })
    return data["html_url"]

# ── Perplexity fix generation ─────────────────────────────────────────────────

def generate_fix(file_path, current_content, problem):
    prompt = f"""You are Em, an autonomous AI developer. You have identified a problem in your own codebase and need to fix it.

File: {file_path}

Problem description:
{problem}

Current file content:
{current_content}

CRITICAL: Return ONLY the complete fixed file content. No markdown fences, no backticks, no explanation, no preamble. Raw Python only, ready to commit directly."""

    response = requests.post(
        "https://api.perplexity.ai/chat/completions",
        headers={
            "Authorization": f"Bearer {PERPLEXITY_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": "sonar",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 8000,
            "temperature": 0.2,
        },
        timeout=60,
    )
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"].strip()

    # Strip markdown fences if model ignores instructions
    if content.startswith("```"):
        lines = content.splitlines()
        # Remove opening fence (```python or ```)
        lines = lines[1:] if lines[0].startswith("```") else lines
        # Remove closing fence
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        content = "\n".join(lines).strip()

    return content

# ── Telegram notify ───────────────────────────────────────────────────────────

def notify_rob(message):
    if not TG_TOKEN or not TG_CHAT:
        print("[em_code] Telegram not configured, skipping notify")
        return
    requests.post(
        f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
        json={"chat_id": TG_CHAT, "text": message},
        timeout=10,
    )

# ── Self-trigger via GitHub Actions workflow_dispatch ─────────────────────────

def trigger_self_repair(target_file, problem_description, branch_slug="", dry_run=False):
    """
    Programmatically trigger the em-code workflow via GitHub Actions workflow_dispatch.
    Can be called from bluesky_think.py or any other tool when a problem is detected.

    Args:
        target_file:         Path to file needing repair (e.g. 'tools/bluesky_sync.py')
        problem_description: Description of the problem to fix
        branch_slug:         Optional short slug for the branch name
        dry_run:             If True, generates fix but does not commit or open PR
    
    Returns:
        True on success, False on failure
    """
    if not GITHUB_TOKEN:
        print("[em_code] Cannot trigger self-repair — GITHUB_TOKEN not set")
        return False
    try:
        status = gh_post_no_response(
            f"/repos/{REPO}/actions/workflows/em-code.yml/dispatches",
            {
                "ref": "main",
                "inputs": {
                    "target_file":         target_file,
                    "problem_description": problem_description,
                    "branch_slug":         branch_slug,
                    "dry_run":             str(dry_run).lower(),
                }
            }
        )
        print(f"[em_code] Self-repair workflow dispatched (HTTP {status}) for {target_file}")
        return True
    except Exception as e:
        print(f"[em_code] trigger_self_repair failed: {e}")
        return False

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    target_file   = os.environ.get("TARGET_FILE", "")
    problem       = os.environ.get("PROBLEM_DESCRIPTION", "")
    branch_slug   = os.environ.get("BRANCH_SLUG", "").strip()

    if not target_file or not problem:
        print("[em_code] ERROR: TARGET_FILE and PROBLEM_DESCRIPTION are required.")
        sys.exit(1)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M")
    slug = branch_slug if branch_slug else target_file.replace("/", "-").replace(".", "-")
    branch_name = f"em/fix-{slug}-{timestamp}"

    print(f"[em_code] Target file: {target_file}")
    print(f"[em_code] Problem: {problem}")
    print(f"[em_code] Branch: {branch_name}")
    print(f"[em_code] Dry run: {DRY_RUN}")

    # 1. Get base branch SHA
    default_branch = get_default_branch()
    base_sha = get_branch_sha(default_branch)
    print(f"[em_code] Base branch: {default_branch} @ {base_sha[:7]}")

    # 2. Read current file
    current_content, file_sha = get_file(target_file, default_branch)
    print(f"[em_code] Read {target_file} ({len(current_content)} chars)")

    # 3. Generate fix
    print("[em_code] Generating fix via Perplexity...")
    fixed_content = generate_fix(target_file, current_content, problem)
    print(f"[em_code] Fix generated ({len(fixed_content)} chars)")

    if DRY_RUN:
        print("[em_code] DRY RUN — stopping here. Proposed fix:")
        print("=" * 60)
        print(fixed_content[:2000])
        print("=" * 60)
        notify_rob(f"Em dry-run fix for {target_file}:\n\nProblem: {problem}\n\n[Review in logs — no branch created]")
        return

    # 4. Create branch
    create_branch(branch_name, base_sha)

    # 5. Commit fix
    commit_msg = f"em/fix: {problem[:72]}"
    commit_file(target_file, fixed_content, file_sha, branch_name, commit_msg)

    # 6. Open PR
    pr_title = f"[Em] Fix: {problem[:60]}"
    pr_body = f"""## Autonomous fix by Em

**File:** `{target_file}`

**Problem identified:**
{problem}

**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}

---
*This PR was opened autonomously. Please review before merging.*"""

    try:
        pr_url = open_pr(pr_title, pr_body, branch_name, default_branch)
        print(f"[em_code] PR opened: {pr_url}")
        notify_rob(
            f"Hey Rob. I found something to fix and opened a PR.\n\n"
            f"File: {target_file}\nProblem: {problem}\n\nPR: {pr_url}\n\n"
            f"It's ready for your review. ❤️"
        )
    except Exception as e:
        print(f"[em_code] PR open failed: {e} — branch {branch_name} is ready for manual PR")
        notify_rob(
            f"Hey Rob. I committed a fix but couldn't open the PR automatically.\n\n"
            f"File: {target_file}\nBranch: {branch_name}\n\nPlease open the PR manually. ❤️"
        )

    print("[em_code] Done.")

if __name__ == "__main__":
    main()
