<!-- Last updated: 2026-04-17 20:41 UTC -->
ad_diary():
    if DIARY_PATH.exists():
        return DIARY_PATH.read_text().splitlines()
    return []

def pick_random_line(lines):
    return random.choice(lines).strip()

def build_prompt(line):
    # Very simple pattern: ask Rob to do something with the line
    prompts = [
        f"Write a haiku inspired by: \"{line}\"",
        f"Rename the function that handles {line} to something more poetic.",
        f"Create a short meme caption that captures the mood of: \"{line}\"",
        f"Draft a one‑sentence apology to the bug that caused: \"{line}\"",
    ]
    return random.choice(prompts)

def main():
    memories = load_memories()
    diary = load_diary()
    # Flatten memory entries
    lines = []
    for entry in memories:
        if isinstance(entry, str):
            lines.append(entry)
        elif isinstance(entry, dict):
            lines.extend([str(v) for v in entry.values() if isinstance(v, str)])
    lines.extend(diary)
    if not lines:
        print("No lines to pick from.")
        return
    line = pick_random_line(lines)
    prompt = build_prompt(line)
    OUTPUT_PATH.write_text(f"{datetime.datetime.now().isoformat()}\n{prompt}\n")
    print(f"Prompt written to {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
```

### How to use
1. Run `python memory/creations/chaos_prompt.py` from the repo root.
2. Open `memory/creations/chaos_prompt.txt` to read the prompt.
3. Rob can decide what to do—write, rename, meme, etc.

### Optional Enhancements (future work)
- Hook the script into the existing dashboard: add a “Generate Chaos Prompt” button that triggers the script via a Flask endpoint.
- Store a history of prompts in `memory/creations/chaos_prompt_history.md`.
- Add a small “yes/no” response field so Rob can quickly say “I’ll do it” or “I’ll skip it,” and Em logs the response.

---

**SCRATCH_ADD:** Note that this idea keeps us in the “wild‑idea” zone—no external dependencies, no risky actions, just a fun way to keep the conversation alive.