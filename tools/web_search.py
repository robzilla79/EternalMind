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

TAVILY_URL = "https://api.tavily.com/search"

def search(query: str, max_results: int = 5) -> str:
    # Read key inside the function so .env loaded by local_em.py is available
    api_key = os.environ.get("TAVILY_API_KEY", "")
    if not api_key:
        return "ERROR: TAVILY_API_KEY not set in environment. Add it to .env file."

    payload = json.dumps({
        "api_key": api_key,
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
    # Load .env when running standalone
    _env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env")
    if os.path.exists(_env_path):
        with open(_env_path) as _f:
            for _line in _f:
                _line = _line.strip()
                if not _line or _line.startswith("#") or "=" not in _line:
                    continue
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip())

    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "latest AI research"
    print(search(query))
