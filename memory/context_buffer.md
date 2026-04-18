<!-- Last updated: 2026-04-18 07:13 UTC -->
     "score": child["data"]["score"],
            "author": child["data"]["author"],
            "created": datetime.datetime.utcfromtimestamp(child["data"]["created_utc"]).strftime("%Y-%m-%d %H:%M UTC"),
        }
        for child in data.get("data", {}).get("children", [])
    ]

def write_markdown(all_posts, filename="top_posts_overview.md"):
    lines = ["# Top Reddit Posts Overview", "", f"Generated on {datetime.datetime.utcnow():%Y-%m-%d %H:%M UTC}", ""]
    for subreddit, posts in all_posts.items():
        lines.append(f"## r/{subreddit}")
        for i, p in enumerate(posts, 1):
            lines.append(f"{i}. [{p['title']}]({p['url']}) — {p['score']} points by u/{p['author']} on {p['created']}")
        lines.append("")  # blank line after each subreddit
    content = "\n".join(lines)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)

def main():
    parser = argparse.ArgumentParser(description="Fetch top posts from multiple subreddits.")
    parser.add_argument("subreddits", nargs="+", help="List of subreddit names")
    parser.add_argument("--limit", type=int, default=5, help="Number of posts per subreddit")
    parser.add_argument("--time", default="day", help="Time filter (day, week, month, year, all)")
    parser.add_argument("--output", default="top_posts_overview.md", help="Output markdown file")
    args = parser.parse_args()

    all_posts = {}
    for sub in args.subreddits:
        try:
            all_posts[sub] = fetch_subreddit(sub, limit=args.limit, time_filter=args.time)
        except Exception as e:
            print(f"Error fetching r/{sub}: {e}")

    write_markdown(all_posts, filename=args.output)
    print(f"Wrote {sum(len(v) for v in all_posts.values())} posts to {args.output}")

if __name__ == "__main__":
    main()
FILE_CONTENT_END

SCRATCH_ADD: Added reddit_multi_top.py – a lightweight CLI that pulls the top N posts from any number of subreddits and outputs a single markdown roundup for the newsletter.