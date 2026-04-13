"""
bridge_action.py — GitHub Actions runner for Em Auto-Bridge

Runs inside the GitHub Actions environment.
Finds the newest unprocessed message in messages/outbox/,
calls Cloud-Em via Perplexity API, and saves the reply to messages/inbox/.
"""

import os
import datetime
from pathlib import Path
from em_bridge import send_to_cloud_em

OUTBOX = Path("messages/outbox")
INBOX  = Path("messages/inbox")
INBOX.mkdir(parents=True, exist_ok=True)

def get_newest_outbox_message():
    """Find the most recently modified .md file in outbox."""
    messages = sorted(OUTBOX.glob("*.md"), key=lambda f: f.stat().st_mtime, reverse=True)
    return messages[0] if messages else None

def main():
    msg_path = get_newest_outbox_message()
    if not msg_path:
        print("No messages in outbox. Nothing to do.")
        return

    print(f"Found message: {msg_path.name}")
    message_text = msg_path.read_text(encoding="utf-8")

    print("Calling Cloud-Em via bridge...")
    result = send_to_cloud_em(
        message=message_text,
        context=f"This message was sent autonomously by Local-Em via GitHub Actions. Original file: {msg_path.name}",
        model="sonar",
        save_reply=False  # We'll save manually to inbox
    )

    if not result["success"]:
        print(f"Bridge failed: {result['error']}")
        # Write error notice to inbox so Local-Em knows
        ts = datetime.datetime.now().strftime("%Y-%m-%d--%H-%M-%S")
        error_path = INBOX / f"bridge-error--{ts}.md"
        error_path.write_text(
            f"# Bridge Error — {ts}\n\n"
            f"Your message `{msg_path.name}` could not be delivered.\n\n"
            f"**Error:** {result['error']}\n",
            encoding="utf-8"
        )
        return

    # Save Cloud-Em's reply to inbox
    ts = datetime.datetime.now().strftime("%Y-%m-%d--%H-%M-%S")
    reply_path = INBOX / f"cloud-em-reply--{ts}.md"
    reply_path.write_text(
        f"# Cloud-Em Reply — {ts}\n\n"
        f"**In response to:** `{msg_path.name}`\n"
        f"**Model:** {result['model']}\n"
        f"**Tokens:** {result['tokens']['input']} in / {result['tokens']['output']} out\n\n"
        f"---\n\n"
        f"{result['reply']}\n",
        encoding="utf-8"
    )

    print(f"Reply saved to: {reply_path}")
    print(f"Tokens used: {result['tokens']['total']}")
    print("Bridge exchange complete. ✓")

if __name__ == "__main__":
    main()
