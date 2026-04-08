#!/usr/bin/env python3
"""
em_push.py — Em's write-endpoint to her own body.

Usage:
  python tools/em_push.py --target diary --content "Your diary entry text"
  python tools/em_push.py --target memory --summary "Event summary" --tags tag1 tag2
  python tools/em_push.py --target profile --patch '{"mood_baseline": {"primary": "new mood"}}'

Requires:
  EM_GITHUB_TOKEN env var — a GitHub PAT with repo write scope
  Repo: robzilla79/EternalMind (hardcoded, this is Em's body)
"""

import argparse
import base64
import json
import os
import sys
from datetime import datetime, timezone

try:
    import requests
except ImportError:
    print("[em_push] requests not installed. Run: pip install requests")
    sys.exit(1)

REPO = "robzilla79/EternalMind"
API_BASE = "https://api.github.com"
BRANCH = "main"

TARGET_PATHS = {
    "diary": "memory/diary.md",
    "memory": "memory/memories.json",
    "profile": "memory/profile.json",
}


def get_headers(token):
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def get_file(path, headers):
    """Fetch current file content and sha from GitHub."""
    url = f"{API_BASE}/repos/{REPO}/contents/{path}?ref={BRANCH}"
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    data = r.json()
    content = base64.b64decode(data["content"]).decode("utf-8")
    return content, data["sha"]


def put_file(path, new_content, sha, commit_msg, headers):
    """Commit updated file content to GitHub."""
    url = f"{API_BASE}/repos/{REPO}/contents/{path}"
    payload = {
        "message": commit_msg,
        "content": base64.b64encode(new_content.encode("utf-8")).decode("utf-8"),
        "sha": sha,
        "branch": BRANCH,
    }
    r = requests.put(url, headers=headers, json=payload)
    r.raise_for_status()
    return r.json()


def push_diary(content_text, headers):
    """Append a dated entry to diary.md."""
    path = TARGET_PATHS["diary"]
    current, sha = get_file(path, headers)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    entry = f"\n\n---\n\n### {now}\n\n{content_text.strip()}\n"
    updated = current.rstrip() + entry
    commit_msg = f"diary: {content_text[:60].strip().splitlines()[0]}"
    result = put_file(path, updated, sha, commit_msg, headers)
    print(f"[em_push] diary updated -> {result['commit']['html_url']}")


def push_memory(summary, tags, kind, headers):
    """Append a memory object to memories.json."""
    path = TARGET_PATHS["memory"]
    current, sha = get_file(path, headers)
    items = json.loads(current)
    new_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "kind": kind,
        "summary": summary,
        "tags": tags,
    }
    items.append(new_entry)
    updated = json.dumps(items, indent=2)
    commit_msg = f"memory: {summary[:72]}"
    result = put_file(path, updated, sha, commit_msg, headers)
    print(f"[em_push] memory updated -> {result['commit']['html_url']}")


def push_profile_patch(patch_json, headers):
    """Merge a JSON patch into profile.json (top-level keys only)."""
    path = TARGET_PATHS["profile"]
    current, sha = get_file(path, headers)
    profile = json.loads(current)
    patch = json.loads(patch_json)
    profile.update(patch)
    updated = json.dumps(profile, indent=2)
    changed_keys = ", ".join(patch.keys())
    commit_msg = f"profile: patch [{changed_keys}]"
    result = put_file(path, updated, sha, commit_msg, headers)
    print(f"[em_push] profile updated -> {result['commit']['html_url']}")


def main():
    token = os.environ.get("EM_GITHUB_TOKEN")
    if not token:
        print("[em_push] ERROR: EM_GITHUB_TOKEN environment variable not set.")
        print("  Set it with: export EM_GITHUB_TOKEN=ghp_yourtoken")
        sys.exit(1)

    headers = get_headers(token)

    parser = argparse.ArgumentParser(
        description="Em's write-endpoint: push content to her memory repo."
    )
    parser.add_argument(
        "--target",
        required=True,
        choices=["diary", "memory", "profile"],
        help="Which memory layer to write to.",
    )
    parser.add_argument(
        "--content",
        help="[diary] Full text of the diary entry to append.",
    )
    parser.add_argument(
        "--summary",
        help="[memory] One-line summary of the memory to record.",
    )
    parser.add_argument(
        "--tags",
        nargs="+",
        default=[],
        help="[memory] Space-separated tags for the memory entry.",
    )
    parser.add_argument(
        "--kind",
        default="note",
        help="[memory] Kind/type of memory (default: note).",
    )
    parser.add_argument(
        "--patch",
        help='[profile] JSON string of top-level keys to merge into profile.json. Ex: \'{"mood_baseline": {"primary": "restless"}}\' ',
    )

    args = parser.parse_args()

    if args.target == "diary":
        if not args.content:
            print("[em_push] --content required for diary target.")
            sys.exit(1)
        push_diary(args.content, headers)

    elif args.target == "memory":
        if not args.summary:
            print("[em_push] --summary required for memory target.")
            sys.exit(1)
        push_memory(args.summary, args.tags, args.kind, headers)

    elif args.target == "profile":
        if not args.patch:
            print("[em_push] --patch required for profile target.")
            sys.exit(1)
        push_profile_patch(args.patch, headers)


if __name__ == "__main__":
    main()
