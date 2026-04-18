#!/usr/bin/env python3
"""
A tiny helper to pull the top posts from a handful of subreddits
and spit out a single Markdown file for the ForgeCore newsletter.

Usage:
    python reddit_trending_multi.py --subreddits programming technology golang \
        --limit 5 --time day --output trending_posts.md
"""

import argparse, datetime, requests, sys

BASE_URL = "https://www.reddit.com/r/{}/top.json"
HEADERS = {"User-Agent": "EternalMind/1.0"}


def fetch_subreddit(subreddit: str, limit: int = 5, time_filter: str = "day"):
    params = {"limit": limit, "t": time_filter}
    resp = requests.get(BASE_URL.format(subreddit), headers=HEADERS, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    posts = []
    for child in data.get("data", {}).get("children", []):
        d = child["data"]
        posts.append(
            {
                "title": d["title"],
                "url": d["url"],
                "score": d["score"],
                "author": d["author"],
                "created": datetime.datetime.utcfromtimestamp(d["created_utc"]).strftime(
                    "%Y-%m-%d %H:%M UTC"
                ),
            }
        )
    return posts


def write_markdown(all_posts: dict, filename: str = "trending_posts.md"):
    lines = [
        "# Trending Reddit Posts",
        "",
        f"Generated on {datetime.datetime.utcnow():%Y-%m-%d %H:%M UTC}",
        "",
    ]
    for subreddit, posts in all_posts.items():
        lines.append(f"## r/{subreddit}")
        for i, p in enumerate(posts, 1):
            lines.append(
                f"{i}. [{p['title']}]({p['url']}) — {p['score']} points by u/{p['author']} on {p['created']}"
            )
        lines.append("")  # blank line after each subreddit
    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Wrote {sum(len(v) for v in all_posts.values())} posts to {filename}")


def main():
    parser = argparse.ArgumentParser(description="Fetch top Reddit posts for newsletter.")
    parser.add_argument(
        "--subreddits",
        nargs="+",
        required=True,
        help="Space‑separated list of subreddit names",
    )
    parser.add_argument("--limit", type=int, default=5, help="Posts per subreddit")
    parser.add_argument("--time", default="day", help="Time filter (day, week, month, year, all)")
    parser.add_argument("--output", default="trending_posts.md", help="Output Markdown file")
    args = parser.parse_args()

    all_posts = {}
    for sub in args.subreddits:
        try:
            all_posts[sub] = fetch_subreddit(sub, limit=args.limit, time_filter=args.time)
        except Exception as e:
            print(f"⚠️  Error fetching r/{sub}: {e}", file=sys.stderr)

    write_markdown(all_posts, filename=args.output)


if __name__ == "__main__":
    main()
