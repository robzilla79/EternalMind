#!/usr/bin/env python3
"""
generate_issue_table.py

A tiny helper that walks the ForgeCore `content/issues` directory,
extracts issue dates and titles from the Markdown files, and prints
a Markdown table ready for inclusion in the daily newsletter.

Usage:
    python generate_issue_table.py

Output example:
| Date       | Title                                 | Link                                 |
|------------|---------------------------------------|--------------------------------------|
| 2026-04-16 | 2026-04-16 — 2026-04-16              | /news/2026-04-16                      |
"""

import pathlib
import re
import sys

ISSUES_DIR = pathlib.Path("content/issues")

def parse_issue_file(path: pathlib.Path):
    """Return (date, title, slug) from a ForgeCore issue file."""
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return None
    title_match = re.search(r"^#\s*(.+)", text, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else "Untitled"
    date_match = re.search(r"(\d{4}-\d{2}-\d{2})", path.name)
    date = date_match.group(1) if date_match else "unknown"
    slug = path.stem  # filename without extension
    return date, title, slug

def main():
    if not ISSUES_DIR.exists():
        print(f"Directory {ISSUES_DIR} not found.", file=sys.stderr)
        sys.exit(1)

    issues = []
    for file in ISSUES_DIR.glob("*.md"):
        parsed = parse_issue_file(file)
        if parsed:
            issues.append(parsed)

    # Sort by date descending
    issues.sort(key=lambda x: x[0], reverse=True)

    # Print Markdown table
    print("| Date       | Title                                 | Link                                 |")
    print("|------------|---------------------------------------|--------------------------------------|")
    for date, title, slug in issues:
        link = f"/news/{slug}"
        print(f"| {date} | {title:<37} | {link:<38} |")

if __name__ == "__main__":
    main()
