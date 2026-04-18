#!/usr/bin/env python3
"""
issue_stats.py

A tiny helper that walks the ForgeCore `content/issues` directory,
counts how many issues were created per day over the last N days,
and prints a Markdown table. Handy for quick analytics or for
including a “daily activity” section in the newsletter.

Usage:
    python issue_stats.py [--days N] [--output path]

Defaults to the last 7 days and prints to stdout.

Example output:

| Date       | Count |
|------------|-------|
| 2026-04-16 | 3     |
| 2026-04-15 | 1     |
"""

import pathlib
import re
import sys
import argparse
from collections import Counter
from datetime import datetime, timedelta

ISSUES_DIR = pathlib.Path("content/issues")

def parse_date_from_filename(path: pathlib.Path):
    """Return a date object extracted from the filename."""
    match = re.search(r"(\d{4}-\d{2}-\d{2})", path.name)
    if match:
        return datetime.strptime(match.group(1), "%Y-%m-%d").date()
    return None

def main():
    parser = argparse.ArgumentParser(description="Count ForgeCore issues per day.")
    parser.add_argument("--days", type=int, default=7,
                        help="Number of past days to include (default 7)")
    parser.add_argument("--output", type=str,
                        help="File to write the table to (default stdout)")
    args = parser.parse_args()

    if not ISSUES_DIR.exists():
        print(f"Directory {ISSUES_DIR} not found.", file=sys.stderr)
        sys.exit(1)

    today = datetime.utcnow().date()
    start_date = today - timedelta(days=args.days - 1)

    counter = Counter()
    for file in ISSUES_DIR.glob("*.md"):
        date = parse_date_from_filename(file)
        if date and start_date <= date <= today:
            counter[date] += 1

    # Sort by date descending
    sorted_dates = sorted(counter.keys(), reverse=True)

    lines = ["| Date       | Count |", "|------------|-------|"]
    for d in sorted_dates:
        lines.append(f"| {d} | {counter[d]} |")

    output = "\n".join(lines)

    if args.output:
        pathlib.Path(args.output).write_text(output, encoding="utf-8")
    else:
        print(output)

if __name__ == "__main__":
    main()
