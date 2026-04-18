<!-- Last updated: 2026-04-18 07:51 UTC -->
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
FILE_CONTENT_END

SCRATCH_ADD: Created reddit_trending_multi.py – pulls top posts from any list of subreddits and outputs a single Markdown roundup for the newsletter.