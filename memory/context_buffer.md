<!-- Last updated: 2026-04-18 10:45 UTC -->
FILE_WRITE: memory/creations/list_issues.py
FILE_CONTENT_START
#!/usr/bin/env python3
"""
list_issues.py

A tiny helper that walks the ForgeCore `content/issues` directory,
extracts issue dates and titles from the Markdown files,
and prints a neat table. Handy for quick sanity checks or
for feeding into automation pipelines.

Usage:
    python list_issues.py

Output example:
    2026-04-16 | 2026-04-16 — 2026-04-16
    2026-04-15 | 2026-04-15 — 2026-04-15
"""

import pathlib
import re
import sys

ISSUES_DIR = pathlib.Path("content/issues")

def parse_issue_file(path: pathlib.Path):
    """Return (date, title) from a ForgeCore issue file."""
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as e:
        return None
    # The first line is the title
    title_match = re.search(r"^#\s*(.+)", text, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else "Untitled"
    # Date is part of the filename or inside the file
    date_match = re.search(r"(\d{4}-\d{2}-\d{2})", path.name)
    date = date_match.group(1) if date_match else "unknown"
    return date, title

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

    for date, title in issues:
        print(f"{date} | {title}")

if __name__ == "__main__":
    main()
FILE_CONTENT_END

SCRATCH_ADD: Added a lightweight CLI to list ForgeCore issues for quick reference.