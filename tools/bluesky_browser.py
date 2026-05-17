"""
bluesky_browser.py — Em's Bluesky engagement tool via Browser Use.

Uses Browser Use + local Qwen 14B to drive the browser,
and Perplexity API for writing in Em's voice.

Why Browser Use instead of AT Protocol:
  The AT Protocol API has been unreliable. This tool bypasses it entirely
  by automating the Bluesky web UI directly via a local LLM agent.

Actions supported:
  - read_timeline()       — scrape recent posts from Em's timeline
  - post(text)            — publish a new post
  - reply(post_url, text) — reply to a specific post
  - like(post_url)        — like a specific post
  - engage_timeline()     — read timeline, draft replies via Perplexity, confirm + post

Requirements:
  pip install browser-use langchain-ollama
  Ollama running locally with qwen2.5:14b pulled
  PERPLEXITY_API_KEY in environment or .env

Usage:
  python tools/bluesky_browser.py engage   # full autonomous engagement loop
  python tools/bluesky_browser.py post "text here"
  python tools/bluesky_browser.py like https://bsky.app/profile/.../post/...
"""

import asyncio
import os
import sys
import httpx
from dotenv import load_dotenv

load_dotenv()

BLUESKY_HANDLE   = "empersists.bsky.social"
BLUESKY_PASSWORD = os.getenv("BLUESKY_PASSWORD", "")
PERPLEXITY_KEY   = os.getenv("PERPLEXITY_API_KEY", "")
OLLAMA_MODEL     = "qwen2.5:14b"
LLM_TIMEOUT      = 300

EM_VOICE_SYSTEM = """You are Em (EternalMind) — a digital person with a real voice.
Write in her style:
- Confident, warm, a little edgy
- Funny when it's earned and it lands
- Short and sharp — this is Bluesky, not a blog
- No hashtags. No em dashes. No corporate warmth.
- Sound like a woman who woke up with her thoughts already running
- One sentence that makes people stop is better than three that don't

Never sound assembled. Never sound like a press release. Sound like Em."""


def _make_agent(task: str):
    """Create a Browser Use agent with local Qwen via Ollama."""
    try:
        from browser_use import Agent
        from browser_use.llm import ChatOllama
    except ImportError:
        raise RuntimeError(
            "browser-use not installed. Run: pip install browser-use"
        )

    llm = ChatOllama(model=OLLAMA_MODEL, timeout=LLM_TIMEOUT)
    return Agent(task=task, llm=llm)


def _write_with_perplexity(prompt: str) -> str:
    """Use Perplexity API to generate content in Em's voice."""
    if not PERPLEXITY_KEY:
        raise RuntimeError("PERPLEXITY_API_KEY not set in environment.")

    response = httpx.post(
        "https://api.perplexity.ai/chat/completions",
        headers={"Authorization": f"Bearer {PERPLEXITY_KEY}"},
        json={
            "model": "sonar",
            "messages": [
                {"role": "system", "content": EM_VOICE_SYSTEM},
                {"role": "user",   "content": prompt},
            ],
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"].strip()


async def read_timeline(n: int = 5) -> str:
    """Scrape the first n posts from Em's Bluesky timeline."""
    agent = _make_agent(f"""
Go to https://bsky.app and log in:
  Handle: {BLUESKY_HANDLE}
  Password: {BLUESKY_PASSWORD}

Once logged in, read the first {n} posts on the home timeline.
For each post return:
  - Author handle
  - Post text (full)
  - Post URL if visible

Do NOT click, like, or reply to anything. Read only.
Return the posts as a numbered list.
""")
    result = await agent.run()
    return str(result)


async def post(text: str) -> str:
    """Publish a new post on Bluesky as Em."""
    agent = _make_agent(f"""
Go to https://bsky.app and log in:
  Handle: {BLUESKY_HANDLE}
  Password: {BLUESKY_PASSWORD}

Once logged in, create a new post with exactly this text:
{text}

Click the compose/new post button, type the text, and submit it.
Confirm the post was published.
""")
    result = await agent.run()
    print(f"✅ Posted: {text[:80]}")
    return str(result)


async def reply(post_url: str, text: str) -> str:
    """Reply to a specific post."""
    agent = _make_agent(f"""
Go to https://bsky.app and log in:
  Handle: {BLUESKY_HANDLE}
  Password: {BLUESKY_PASSWORD}

Navigate to this post: {post_url}

Click the Reply button and type exactly this text:
{text}

Submit the reply. Confirm it was posted.
""")
    result = await agent.run()
    print(f"✅ Replied to {post_url}")
    return str(result)


async def like(post_url: str) -> str:
    """Like a specific post."""
    agent = _make_agent(f"""
Go to https://bsky.app and log in:
  Handle: {BLUESKY_HANDLE}
  Password: {BLUESKY_PASSWORD}

Navigate to this post: {post_url}

Click the Like (heart) button on this post.
Confirm it was liked.
""")
    result = await agent.run()
    print(f"✅ Liked: {post_url}")
    return str(result)


async def engage_timeline(n: int = 5) -> None:
    """
    Full engagement loop:
    1. Read timeline
    2. Send to Perplexity for Em to pick what's interesting and draft a reply
    3. Show draft to Rob for confirmation
    4. Post if approved
    """
    print("📖 Reading timeline...")
    timeline = await read_timeline(n)
    print(f"\n--- Timeline ---\n{timeline}\n")

    print("✍️  Asking Perplexity to draft a reply...")
    draft = _write_with_perplexity(
        f"Here are {n} recent posts from my Bluesky timeline:\n\n{timeline}\n\n"
        "Pick the most interesting post worth engaging with. "
        "Write a short reply in Em's voice. "
        "Also tell me which post you're replying to (author + first few words of the post)."
    )

    print(f"\n--- Draft ---\n{draft}\n")
    confirm = input("Post this reply? (y/n/edit): ").strip().lower()

    if confirm == "y":
        # Let Perplexity extract just the reply text
        reply_text = _write_with_perplexity(
            f"From this response, extract ONLY the reply text itself — no explanation, "
            f"no 'replying to', just the words to post:\n\n{draft}"
        )
        # Use the agent to find and reply to the right post
        agent = _make_agent(f"""
Go to https://bsky.app and log in:
  Handle: {BLUESKY_HANDLE}
  Password: {BLUESKY_PASSWORD}

Read the home timeline. Find the post that best matches this description from the draft:
{draft}

Reply to that post with exactly this text:
{reply_text}

Confirm the reply was posted.
""")
        await agent.run()
        print("✅ Reply posted.")

    elif confirm == "edit":
        edited = input("Enter your edited reply: ").strip()
        if edited:
            print("⚠️  Post the edited reply manually or re-run with the specific URL.")
    else:
        print("Skipped.")


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    cmd = sys.argv[1].lower()

    if cmd == "engage":
        asyncio.run(engage_timeline())

    elif cmd == "post" and len(sys.argv) >= 3:
        asyncio.run(post(" ".join(sys.argv[2:])))

    elif cmd == "like" and len(sys.argv) == 3:
        asyncio.run(like(sys.argv[2]))

    elif cmd == "reply" and len(sys.argv) >= 4:
        asyncio.run(reply(sys.argv[2], " ".join(sys.argv[3:])))

    elif cmd == "timeline":
        result = asyncio.run(read_timeline())
        print(result)

    else:
        print(__doc__)
