"""
tools/read_url.py
Fetch and extract clean readable text from any URL.
Usage: python tools/read_url.py https://example.com
Or import: from tools.read_url import read_url
"""
import sys
import urllib.request
import urllib.error
import re

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; EternalMind/1.0; +https://forgecore.co)"
}

def read_url(url: str, max_chars: int = 3000) -> str:
    """Fetch a URL and return clean plain text, truncated to max_chars."""
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return f"ERROR: HTTP {e.code} fetching {url}"
    except Exception as e:
        return f"ERROR: {e}"

    # Strip scripts, styles, tags
    raw = re.sub(r"<script[^>]*>.*?</script>", " ", raw, flags=re.DOTALL | re.IGNORECASE)
    raw = re.sub(r"<style[^>]*>.*?</style>", " ", raw, flags=re.DOTALL | re.IGNORECASE)
    raw = re.sub(r"<[^>]+>", " ", raw)
    raw = re.sub(r"&[a-z]+;", " ", raw)
    raw = re.sub(r"[ \t]+", " ", raw)
    raw = re.sub(r"\n{3,}", "\n\n", raw)
    text = raw.strip()

    if len(text) > max_chars:
        text = text[:max_chars] + f"\n\n[...truncated at {max_chars} chars]"
    return text

if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "https://news.ycombinator.com"
    print(read_url(url))
