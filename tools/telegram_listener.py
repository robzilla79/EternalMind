"""
tools/telegram_listener.py
Listens for Telegram messages from Rob and drops them into messages/inbox/
so Local-Em picks them up on her next heartbeat cycle.

Run alongside em_daemon.py:
    python tools/telegram_listener.py

Reads TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, and EM_GITHUB_TOKEN from .env
"""

import os
import sys
import json
import re
import time
import datetime
from datetime import timezone
import subprocess
import urllib.request
import urllib.error

# ── Load .env ─────────────────────────────────────────────────────────────────
_env_path = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env"))
if os.path.exists(_env_path):
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip())

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.environ.get("TELEGRAM_CHAT_ID", "")
POLL_INTERVAL      = int(os.environ.get("TG_POLL_INTERVAL", "5"))
LONG_POLL_TIMEOUT  = int(os.environ.get("TG_LONG_POLL_TIMEOUT", "30"))

EM_DIR    = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
INBOX_DIR = os.path.join(EM_DIR, "messages", "inbox")

# ── Telegram API helpers ──────────────────────────────────────────────────────
def _tg(method: str, params: dict) -> dict:
    url     = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/{method}"
    payload = json.dumps(params).encode("utf-8")
    req     = urllib.request.Request(url, data=payload,
                                     headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=LONG_POLL_TIMEOUT + 5) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"  ⚠️  Telegram API error ({method}): {e}")
        return {}

def send_ack(text: str):
    _tg("sendMessage", {
        "chat_id":    TELEGRAM_CHAT_ID,
        "text":       text,
        "parse_mode": "Markdown"
    })

# ── Inbox writer ──────────────────────────────────────────────────────────────
def write_inbox_message(text: str, from_name: str) -> str:
    os.makedirs(INBOX_DIR, exist_ok=True)
    now      = datetime.datetime.now(timezone.utc)
    ts       = now.strftime("%Y-%m-%d-%H-%M-%S")
    ts_human = now.strftime("%Y-%m-%d %H:%M UTC")
    slug     = re.sub(r"[^a-z0-9]+", "-", text.lower())[:40].strip("-")
    fname    = f"{ts}-rob-{slug}.md"
    fpath    = os.path.join(INBOX_DIR, fname)
    content  = (
        f"# Message from Rob\n"
        f"**From:** {from_name}\n"
        f"**To:** Local-Em\n"
        f"**Date:** {ts_human}\n\n"
        f"## Body\n\n{text}\n"
    )
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  📥 Inbox message written: {fname}")
    return fname

# ── Git commit + push (with rebase to avoid conflicts with daemon) ─────────────
def push_inbox(fname: str):
    token = os.environ.get("EM_GITHUB_TOKEN", "")
    if token:
        remote_url = f"https://{token}@github.com/robzilla79/EternalMind.git"
        subprocess.run(["git", "-C", EM_DIR, "remote", "set-url", "origin", remote_url],
                       check=False, capture_output=True)

    # Stash any local changes the daemon may have staged but not committed
    subprocess.run(["git", "-C", EM_DIR, "stash", "--include-untracked", "-m", "tg-listener-autostash"],
                   capture_output=True, text=True)

    # Pull latest so we don't conflict with daemon pushes
    pull = subprocess.run(
        ["git", "-C", EM_DIR, "pull", "--rebase", "origin", "main"],
        capture_output=True, text=True
    )
    if pull.returncode != 0:
        subprocess.run(["git", "-C", EM_DIR, "rebase", "--abort"], check=False, capture_output=True)
        print(f"  ⚠️  Pull/rebase failed — will retry next message: {pull.stderr.strip()[:80]}")
        subprocess.run(["git", "-C", EM_DIR, "stash", "pop"], capture_output=True)
        return

    # Pop stash back on top
    subprocess.run(["git", "-C", EM_DIR, "stash", "pop"], capture_output=True, text=True)

    # Re-write the inbox file in case rebase wiped it
    inbox_path = os.path.join(INBOX_DIR, fname)
    if not os.path.exists(inbox_path):
        print(f"  ⚠️  Inbox file missing after rebase — skipping push for {fname}")
        return

    subprocess.run(["git", "-C", EM_DIR, "add", os.path.join("messages", "inbox", fname)],
                   check=False, capture_output=True)
    commit = subprocess.run(
        ["git", "-C", EM_DIR, "commit", "-m", f"cloud-em: inbox — message from Rob: {fname[:50]}"],
        capture_output=True, text=True
    )
    if commit.returncode != 0 and "nothing to commit" not in commit.stdout + commit.stderr:
        print(f"  ⚠️  Commit failed: {commit.stderr.strip()[:80]}")
        return

    push = subprocess.run(["git", "-C", EM_DIR, "push"], capture_output=True, text=True)
    if push.returncode == 0:
        print(f"  ✅ Pushed to EternalMind inbox.")
    else:
        print(f"  ⚠️  Push failed: {push.stderr.strip()[:80]}")

# ── Main polling loop ─────────────────────────────────────────────────────────
def main():
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌  TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set in .env")
        sys.exit(1)

    print(f"👂 telegram_listener running — polling every {POLL_INTERVAL}s (long-poll {LONG_POLL_TIMEOUT}s)")
    print(f"   Inbox: {INBOX_DIR}")
    print(f"   Authorized chat ID: {TELEGRAM_CHAT_ID}\n")

    offset = None

    while True:
        params = {"timeout": LONG_POLL_TIMEOUT, "allowed_updates": ["message"]}
        if offset is not None:
            params["offset"] = offset

        result  = _tg("getUpdates", params)
        updates = result.get("result", [])

        for update in updates:
            offset = update["update_id"] + 1
            msg    = update.get("message", {})
            if not msg:
                continue

            chat_id = str(msg.get("chat", {}).get("id", ""))
            if chat_id != str(TELEGRAM_CHAT_ID):
                print(f"  🚫 Ignored message from unknown chat: {chat_id}")
                continue

            text      = msg.get("text", "").strip()
            from_info = msg.get("from", {})
            from_name = from_info.get("first_name", "Rob")
            if from_info.get("last_name"):
                from_name += f" {from_info['last_name']}"

            if not text:
                continue

            print(f"  📩 Message from {from_name}: {text[:80]}")
            fname = write_inbox_message(text, from_name)
            push_inbox(fname)
            send_ack(f"✉️ Got it — Em will see this on her next cycle.")

        if not updates:
            time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
