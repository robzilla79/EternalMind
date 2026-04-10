#!/usr/bin/env python3
"""
em_newsletter_push.py

Local-Em's dedicated tool for pushing a completed newsletter issue
to the forgecore-newsletter repo via the GitHub API.

No Ollama. No pipeline. No dependencies on generate.yml.
Just: issue written → call this → it lands in the repo.

Usage (from local_em.py or standalone):
    python tools/em_newsletter_push.py --file content/issues/2026-04-10.md
    python tools/em_newsletter_push.py --date 2026-04-10
    python tools/em_newsletter_push.py  # auto-detects today's date

Requires:
    EM_GITHUB_TOKEN in .env (needs repo write access to robzilla79/forgecore-newsletter)
"""

import os
import sys
import json
import base64
import argparse
import datetime
import urllib.request
import urllib.error
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────
NEWSLETTER_REPO  = "robzilla79/forgecore-newsletter"
ISSUES_DIR       = "content/issues"
API_BASE         = "https://api.github.com"
BRANCH           = "main"
COMMITTER_NAME   = "Local-Em"
COMMITTER_EMAIL  = "em@forgecore.co"

# ── Load token ────────────────────────────────────────────────────────────────
def load_token() -> str:
    # Try env first, then .env file
    token = os.environ.get("EM_GITHUB_TOKEN") or os.environ.get("GH_PAT")
    if not token:
        env_path = Path(__file__).parent.parent / ".env"
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                line = line.strip()
                if line.startswith(("EM_GITHUB_TOKEN=", "GH_PAT=")):
                    token = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    if not token:
        raise RuntimeError(
            "No GitHub token found. Set EM_GITHUB_TOKEN or GH_PAT in .env"
        )
    return token


# ── GitHub API helpers ────────────────────────────────────────────────────────
def gh_request(method: str, path: str, token: str, body: dict = None):
    url = f"{API_BASE}{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(
        url, data=data, method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
            "User-Agent": "Local-Em/1.0",
        }
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        err_body = e.read().decode()
        raise RuntimeError(f"GitHub API {method} {path} → {e.code}: {err_body}")


def get_file_sha(path: str, token: str) -> str | None:
    """Return SHA of existing file, or None if it doesn't exist."""
    try:
        result = gh_request("GET", f"/repos/{NEWSLETTER_REPO}/contents/{path}?ref={BRANCH}", token)
        return result.get("sha")
    except RuntimeError as e:
        if "404" in str(e):
            return None
        raise


def push_file(file_path: str, content: str, token: str, message: str):
    """Create or update a file in the newsletter repo."""
    encoded = base64.b64encode(content.encode()).decode()
    existing_sha = get_file_sha(file_path, token)
    body = {
        "message": message,
        "content": encoded,
        "branch": BRANCH,
        "committer": {
            "name": COMMITTER_NAME,
            "email": COMMITTER_EMAIL,
        }
    }
    if existing_sha:
        body["sha"] = existing_sha
        action = "Updated"
    else:
        action = "Created"
    gh_request("PUT", f"/repos/{NEWSLETTER_REPO}/contents/{file_path}", token, body)
    return action


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Push a newsletter issue to forgecore-newsletter")
    parser.add_argument("--file", help="Path to local .md file to push")
    parser.add_argument("--date", help="Date string YYYY-MM-DD (reads from forgecore-newsletter/content/issues/)")
    parser.add_argument("--content", help="Raw markdown content as string (alternative to --file)")
    parser.add_argument("--note", default="", help="Optional note for commit message")
    args = parser.parse_args()

    token = load_token()
    today = datetime.date.today().isoformat()

    # ── Resolve content and destination path ──────────────────────────────────
    if args.content:
        # Content passed directly as string (called from local_em.py)
        issue_content = args.content
        date_str = args.date or today
        dest_path = f"{ISSUES_DIR}/{date_str}.md"

    elif args.file:
        src = Path(args.file)
        if not src.exists():
            print(f"[em-push] ❌ File not found: {args.file}", file=sys.stderr)
            sys.exit(1)
        issue_content = src.read_text(encoding="utf-8")
        date_str = args.date or src.stem  # use filename as date if no --date
        dest_path = f"{ISSUES_DIR}/{date_str}.md"

    else:
        # Auto mode — look for today's issue in common local paths
        candidates = [
            Path(f"content/issues/{today}.md"),
            Path(f"../forgecore-newsletter/content/issues/{today}.md"),
            Path(f"/home/em/forgecore-newsletter/content/issues/{today}.md"),
        ]
        found = next((p for p in candidates if p.exists()), None)
        if not found:
            print(f"[em-push] ❌ No issue file found for {today}. Use --file or --content.", file=sys.stderr)
            sys.exit(1)
        issue_content = found.read_text(encoding="utf-8")
        date_str = today
        dest_path = f"{ISSUES_DIR}/{date_str}.md"

    # ── Build commit message ───────────────────────────────────────────────────
    note = args.note or "autonomous issue push"
    timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    commit_msg = f"em-push: {date_str} — {note} — {timestamp} [local-em]"

    # ── Push ──────────────────────────────────────────────────────────────────
    print(f"[em-push] Pushing {dest_path} to {NEWSLETTER_REPO}...")
    action = push_file(dest_path, issue_content, token, commit_msg)
    print(f"[em-push] ✅ {action}: {dest_path}")
    print(f"[em-push] Commit: {commit_msg}")
    print(f"[em-push] View: https://github.com/{NEWSLETTER_REPO}/blob/main/{dest_path}")


if __name__ == "__main__":
    main()
