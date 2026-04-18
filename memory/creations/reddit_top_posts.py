import requests, datetime

def fetch_top_posts(subreddit='programming', limit=10, time_filter='day'):
    url = f'https://www.reddit.com/r/{subreddit}/top.json?limit={limit}&t={time_filter}'
    headers = {'User-Agent': 'EternalMind/1.0'}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    data = resp.json()
    posts = []
    for child in data['data']['children']:
        post = child['data']
        posts.append({
            'title': post['title'],
            'url': post['url'],
            'score': post['score'],
            'author': post['author'],
            'created_utc': datetime.datetime.utcfromtimestamp(post['created_utc']).strftime('%Y-%m-%d %H:%M UTC')
        })
    return posts

def write_markdown(posts, filename='top_programming_posts.md'):
    lines = ['# Top r/programming Posts', '', f'Generated on {datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")}', '']
    for i, p in enumerate(posts, 1):
        lines.append(f'{i}. [{p["title"]}]({p["url"]}) — {p["score"]} points by u/{p["author"]} on {p["created_utc"]}')
    content = '\n'.join(lines)
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == '__main__':
    posts = fetch_top_posts()
    write_markdown(posts)
    print(f'Wrote {len(posts)} posts to top_programming_posts.md')
