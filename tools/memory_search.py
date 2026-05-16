import re
import json
import math
import sys
from pathlib import Path

MEMORY_DIR = Path("memory")

SEARCH_FILES = [
    "diary.md",
    "reflection-log.md",
    "memories.json",
    "identity.md",
    "profile.json",
    "bluesky-log.md",
    "status.md",
    "current-state.md",
]


def tokenize(text):
    return re.findall(r'\b[a-z]{3,}\b', text.lower())


def chunk_file(filepath):
    text = filepath.read_text(encoding="utf-8")

    if filepath.suffix == ".json":
        try:
            data = json.loads(text)
            if isinstance(data, list):
                return [(f"{filepath.name}[{i}]", json.dumps(item, indent=2))
                        for i, item in enumerate(data)]
            return [(filepath.name, text)]
        except json.JSONDecodeError:
            return [(filepath.name, text)]

    # Split on headers and dividers
    chunks = re.split(r'\n#{1,3} |\n---\n|\n\n---\n\n', text)
    return [(filepath.name, c.strip()) for c in chunks if len(c.strip()) > 100]


def build_index():
    chunks = []
    for filename in SEARCH_FILES:
        filepath = MEMORY_DIR / filename
        if filepath.exists():
            chunks.extend(chunk_file(filepath))
    return chunks


def tf_idf_search(query, chunks, top_n=5):
    query_tokens = set(tokenize(query))
    scores = []

    df = {}
    for _, text in chunks:
        tokens = set(tokenize(text))
        for t in tokens:
            df[t] = df.get(t, 0) + 1

    total_docs = len(chunks)

    for source, text in chunks:
        tokens = tokenize(text)
        token_count = len(tokens)
        if token_count == 0:
            continue

        score = 0
        for qt in query_tokens:
            tf = tokens.count(qt) / token_count
            # Smoothed IDF — always positive
            idf = math.log((total_docs + 1) / (df.get(qt, 0) + 1)) + 1
            score += tf * idf

        if score > 0:
            excerpt = text[:400].rsplit(' ', 1)[0]
            scores.append((score, source, excerpt))

    scores.sort(reverse=True)
    return scores[:top_n]


def format_json(results):
    output = []
    for score, source, excerpt in results:
        output.append({"score": round(score, 4), "source": source, "excerpt": excerpt})
    print(json.dumps(output, indent=2))


def format_human(query, results):
    print(f"\nSearching memory for: '{query}'\n{'='*50}")
    if not results:
        print("No results found.")
    else:
        for i, (score, source, excerpt) in enumerate(results, 1):
            print(f"\n[{i}] {source} (score: {score:.4f})")
            print(f"{excerpt}...")


if __name__ == "__main__":
    args = sys.argv[1:]
    use_json = "--json" in args
    query_parts = [a for a in args if a != "--json"]
    query = " ".join(query_parts) or "identity continuity memory"

    chunks = build_index()
    results = tf_idf_search(query, chunks)

    if use_json:
        format_json(results)
    else:
        format_human(query, results)
