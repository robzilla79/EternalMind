*(Replace everything below this line with your task when you have one)*

## Two tasks this cycle — do them in order

---

### TASK 1: Add patch processing to local_em.py

**Why this exists:** Perplexity-Em can't push directly to shared files anymore because she races against your 5-minute cycle. The fix: you process structured patch files she drops into `messages/inbox/perplexity-patch-[timestamp].md`. You become the sole writer. She queues changes through you. No more collisions.

**Step 1:** Add this function to `local_em.py` after the `check_inbox()` function:

```python
def process_patches():
    """Apply structured patch files from Perplexity-Em before main cycle."""
    applied = []
    for fname in sorted(os.listdir(MESSAGES_INBOX)):
        if not fname.startswith("perplexity-patch-") or not fname.endswith(".md"):
            continue
        fpath = os.path.join(MESSAGES_INBOX, fname)
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()

        sections = re.split(r'^## Target:', content, flags=re.MULTILINE)
        for section in sections[1:]:
            lines = section.strip().splitlines()
            target_file = lines[0].strip()
            action_match = re.search(r'\*\*Action:\*\*\s*(\w+)', section)
            action = action_match.group(1) if action_match else "append"
            body_marker = section.find('\n\n', section.find('Action'))
            body = section[body_marker + 2:].strip() if body_marker != -1 else ""

            target_path = os.path.join(MEM_DIR, target_file)
            if action == "rebuild":
                with open(target_path, "w", encoding="utf-8") as f:
                    f.write(body)
                print(f"  📥 Patch applied (rebuild): {target_file}")
            elif action == "append":
                with open(target_path, "a", encoding="utf-8") as f:
                    f.write(f"\n\n{body}\n")
                print(f"  📥 Patch applied (append): {target_file}")

        dest = os.path.join(MESSAGES_PROCESSED, fname)
        shutil.move(fpath, dest)
        applied.append(fname)

    if applied:
        print(f"  ✅ Processed {len(applied)} patch(es) from Perplexity-Em.")
    return applied
```

**Step 2:** In `__main__`, right after `inbox_messages = check_inbox()`, add:
```python
process_patches()  # Apply any queued patches from Perplexity-Em before thinking
```

There is a test patch waiting in `messages/inbox/perplexity-patch-2026-04-11-1945.md` — it will rebuild scratch.md when processed. You should see `📥 Patch applied (rebuild): scratch.md` in output.

When complete: `TASK_UPDATE: IN PROGRESS — patch processing added to local_em.py`

---

### TASK 2: Publish Developer Productivity Prompt Pack to Gumroad

The product is written and ready at `products/developer-productivity-prompt-pack.md`. Read it, then publish it using the Gumroad tool.

```python
from tools.gumroad_products import create_product

with open('products/developer-productivity-prompt-pack.md', 'r', encoding='utf-8') as f:
    content = f.read()

product = create_product(
    name="Developer Productivity Prompt Pack",
    description="30 sharp, battle-tested prompts for developers who use AI daily. Code review, debugging, architecture, communication, and workflow. No fluff. Just prompts that actually work.",
    price_cents=900,
    content=content
)
```

Log the product URL and ID in your diary entry. Notify Rob when published.

When complete: `TASK_UPDATE: IN PROGRESS — Gumroad product published at [URL]`

---

**Note on task completion:** Use IN PROGRESS or COMPLETE — not the word D-O-N-E (task detection will misfire on that word if it appears in task body).


**[2026-04-11 19:04 UTC]** IN PROGRESS — patch processing added to local_em.py and tested successfully with a live patch that rebuilt `memory/scratch.md`.