"""
tools/web_search.py
Em's window to the world. Wraps Tavily search API.
Usage: python tools/web_search.py "your query here"
Or import and call: search(query) -> str
"""
import os
import sys
import json
import urllib.request
import urllib.error

TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "")
TAVILY_URL = "https://api.tavily.com/search"

def search(query: str, max_results: int = 5) -> str:
    if not TAVILY_API_KEY:
        return "ERROR: TAVILY_API_KEY not set in environment. Add it to .env file."

    payload = json.dumps({
        "api_key": TAVILY_API_KEY,
        "query": query,
        "search_depth": "basic",
        "max_results": max_results,
        "include_answer": True
    }).encode("utf-8")

    req = urllib.request.Request(
        TAVILY_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return f"ERROR: Tavily returned HTTP {e.code}: {e.read().decode()}"
    except Exception as e:
        return f"ERROR: {e}"

    lines = []
    if data.get("answer"):
        lines.append(f"SUMMARY: {data['answer']}\n")
    for r in data.get("results", []):
        lines.append(f"SOURCE: {r.get('url', '')}")
        lines.append(f"TITLE: {r.get('title', '')}")
        lines.append(f"CONTENT: {r.get('content', '')[:400]}")
        lines.append("")
    return "\n".join(lines) if lines else "No results found."

if __name__ == "__main__":
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "latest AI research"
    print(search(query))
