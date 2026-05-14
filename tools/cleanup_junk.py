#!/usr/bin/env python3
"""
One-shot cleanup script — deletes junk files from memory/creations/ and memory/research/
Run: GITHUB_TOKEN=your_token python tools/cleanup_junk.py
"""

import os
import requests

TOKEN = os.environ["GITHUB_TOKEN"]
OWNER = "robzilla79"
REPO = "EternalMind"
BRANCH = "main"
HEADERS = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github+json"
}

JUNK_FILES = [
    "memory/creations/forgecore-idempotency-prototype.py",
    "memory/creations/forgecore-redis-module.py",
    "memory/creations/forgecore.sh",
    "memory/creations/forgecore_cli.py",
    "memory/creations/forgecore_readme.md",
    "memory/creations/redis-benchmark-setup.sh",
    "memory/creations/redis-cluster-docker-compose.yml",
    "memory/creations/redis-custom-metrics.sh",
    "memory/creations/redis-exporter-custom.yaml",
    "memory/creations/redis-exporter-setup.md",
    "memory/creations/redis-load-test.sh",
    "memory/creations/redis_hotkeys_monitor.py",
    "memory/creations/redis_monitoring_locust.py",
    "memory/creations/redis_streams_101.md",
    "memory/creations/redis_streams_event_sourcing.md",
    "memory/creations/redis_streams_phi_test.py",
    "memory/creations/redis_streams_phi_test_modified.py",
    "memory/creations/redis_streams_phi_test_v2.py",
    "memory/creations/redis_streams_vs_kafka.md",
    "memory/creations/xautoclaim-stress-test-lua.lua",
    "memory/creations/prometheus-config.yml",
    "memory/creations/inject_phi_data.py",
    "memory/creations/phi_validator.py",
    "memory/creations/synthetic_phi_dataset.py",
    "memory/creations/synthetic_psa_datasets.py",
    "memory/creations/synthetic_workload_script.py",
    "memory/creations/dashboard-app.py",
    "memory/creations/dashboard.html",
    "memory/creations/duplicate_write_guard.py",
    "memory/creations/dynamic_maxlen_script.py",
    "memory/creations/generate_issue_table.py",
    "memory/creations/issue_stats.py",
    "memory/creations/list_issues.py",
    "memory/creations/locust-test.py",
    "memory/creations/browser-test-report.md",
    "memory/creations/index.html",
    "memory/creations/requirements.txt",
    "memory/creations/2026-04-13--personal-portfolio-template.html",
    "memory/creations/user-guide.md",
    "memory/creations/reddit_multi_top.py",
    "memory/creations/reddit_top_posts.py",
    "memory/creations/reddit_trending_multi.py",
    "memory/creations/gumroad_test.log",
    "memory/research/forgecore-audit-plan.md",
    "memory/research/forgecore-audit.md",
    "memory/research/forgecore-openclaw-integration.md",
    "memory/research/forgecore-redis-integration.md",
]


def get_sha(path):
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{path}?ref={BRANCH}"
    r = requests.get(url, headers=HEADERS)
    if r.status_code == 200:
        return r.json()["sha"]
    print(f"  SKIP (not found): {path}")
    return None


def delete_file(path, sha):
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{path}"
    payload = {
        "message": f"chore: delete junk file {path}",
        "sha": sha,
        "branch": BRANCH
    }
    r = requests.delete(url, headers=HEADERS, json=payload)
    if r.status_code == 200:
        print(f"  DELETED: {path}")
        return True
    print(f"  FAILED ({r.status_code}): {path} — {r.text[:120]}")
    return False


if __name__ == "__main__":
    print(f"Starting cleanup — {len(JUNK_FILES)} files targeted\n")
    deleted = 0
    skipped = 0
    failed = 0
    for path in JUNK_FILES:
        sha = get_sha(path)
        if sha:
            if delete_file(path, sha):
                deleted += 1
            else:
                failed += 1
        else:
            skipped += 1
    print(f"\nDone. Deleted: {deleted} | Skipped: {skipped} | Failed: {failed}")
