```python
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
from typing import Optional, Dict, Any

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

def gh_get(path: str) -> Dict[str, Any]:
    r = requests.get(f"{GH_API}{path}", headers=GH_HDRS, timeout=20)
    r.raise_for_status()
    return r.json()

def gh_post(path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    r = requests.post(f"{GH_API}{path}", headers=GH_HDRS, json=payload, timeout=20)
    r.raise_for_status()
    return r.json()

def gh_put(path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    r = requests.put(f"{GH_API}{path}", headers=GH_HDRS, json=payload, timeout=20)
    r.raise_for_status()
    return r.json()

def get_default_branch() -> str:
    data = gh_get(f"/repos/{REPO}")
    return data["default_branch"]

def get_branch_sha(branch: str) -> str:
    data = gh_get(f"/repos/{REPO}/git/ref/heads/{branch}")
    return data["object"]["sha"]

def create_branch(branch_name: str, from_sha: str) -> None:
    gh_post(f"/repos/{REPO}/git/refs", {
        "ref": f"refs/heads/{branch_name}",
        "sha": from_sha,
    })
    print(f"[em_code] Created branch: {branch_name}")

def get_file(path: str, branch: str) -> tuple[str, str]:
    data = gh_get(f"/repos/{REPO}/contents/{path}?ref={branch}")
    content = base64.b64decode(data["content"]).decode("utf-8")
    return content, data["sha"]

def commit_file(path: str, content: str, file_sha: str, branch: str, message: str) -> None:
    encoded = base64.b64encode(content.encode("utf-8")).decode("utf-8")
    gh_put(f"/repos/{REPO}/contents/{path}", {
        "message": message,
        "content": encoded,
        "sha": file_sha,
        "branch": branch,
    })
    print(f"[em_code] Committed fix to {path} on {branch}")

def open_pr(title: str, body: str, head: str, base: str) -> str:
    data = gh_post(f"/repos/{REPO}/pulls", {
        "title": title,
        "body": body,
        "head": head,
        "base": base,
    })
    return data["html_url"]

# ── Perplexity fix generation ─────────────────────────────────────────────────

def generate_fix(file_path: str, current_content: str, problem: str) -> str:
    prompt = f"""You are Em, an autonomous AI developer. You have identified a problem in your own codebase and need to fix it.

File: {file_path}

Problem description:
{problem}

Current file content:
```
{current_content}
```

Please return ONLY the complete fixed file content, with no explanation, no markdown code fences, no preamble. Just the raw fixed file, ready to commit."""

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
    return response.json()["choices"][0]["message"]["content"].strip()

# ── Telegram notify ───────────────────────────────────────────────────────────

def notify_rob(message: str) -> None:
    if not TG_TOKEN or not TG_CHAT:
        print("[em_code] Telegram not configured, skipping notify")
        return
    requests.post(
        f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
        json={"chat_id": TG_CHAT, "text": message},
        timeout=10,
    )

# ── Self-trigger via GitHub Actions workflow_dispatch ─────────────────────────

def trigger_self_repair(
    target_file: str,
    problem_description: str,
    branch_slug: str = "",
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Programmatically trigger em_code.py via GitHub Actions workflow_dispatch.
    
    Args:
        target_file: Path to file needing repair (e.g. "tools/em_code.py")
        problem_description: Description of the problem to fix
        branch_slug: Optional branch slug for PR naming
        dry_run: Whether to run in dry-run mode
    
    Returns:
        Dict containing workflow run details
    """
    if not GITHUB_TOKEN:
        raise ValueError("GITHUB_TOKEN environment variable required")
    
    workflow_id = ".github/workflows/em-code.yml"
    
    payload = {
        "ref": get_default_branch(),
        "inputs": {
            "TARGET_FILE": target_file,
            "PROBLEM_DESCRIPTION": problem_description,
            "BRANCH_SLUG": branch_slug,
            "DRY_RUN": str(dry_run).lower()
        }
    }
    
    response = gh_post(f"/repos/{REPO}/actions/workflows/{workflow_id}/dispatches", payload)
    
    print(f"[em_code] Triggered self-repair workflow: {response['html_url']}")
    return response

# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
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

    pr_url = open_pr(pr_title, pr_body, branch_name, default_branch)
    print(f"[em_code] PR opened: {pr_url}")

    # 7. Notify Rob
    notify_rob(
        f"Hey Rob. I found something to fix and opened a PR.\n\n"
        f"File: {target_file}\nProblem: {problem}\n\nPR: {pr_url}\n\n"
        f"It's ready for your review. ❤️"
    )

    print("[em_code] Done.")

if __name__ == "__main__":
    main()
```