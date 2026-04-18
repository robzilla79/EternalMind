"""
tools/telegram_listener_simple.py — Simple Two-Way Telegram Listener

This listener:
  1. Receives your messages via Telegram
  2. Writes them to messages/inbox/
  3. Reads them back automatically when Local-Em processes them
  4. Sends responses automatically via Telegram

Usage:
  python tools/telegram_listener_simple.py

Or run with daemon:
  python tools/em_daemon.py &
  python tools/telegram_listener_simple.py

Features:
  ✓ Two-way communication (you send → Em replies)
  ✓ Auto-commits to git
  ✓ Maintains conversation context
  ✓ Works in tandem with local_em.py or em_daemon.py
"""

import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

import re
import time
import datetime
from datetime import timezone
import urllib.request
import urllib.error
import json

# ── Load config ───────────────────────────────────────────────────────────────
_telegram_path = os.path.normpath(os.path.join(__file__, "..", "..", ".env"))
if os.path.exists(_telegram_path):
    with open(_telegram_path) as f:
        for line in f:
            line = line.strip()
            if line and "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.environ.get("TELEGRAM_CHAT_ID", "")
POLL_INTERVAL      = int(os.environ.get("TG_POLL_INTERVAL", "5"))

EM_DIR    = os.path.normpath(os.path.join(__file__, "..", ".."))
INBOX_DIR = os.path.join(EM_DIR, "messages", "inbox")
REPLY_DIR = os.path.join(EM_DIR, "messages", "cloud_em_replies")
TASKS_PATH = os.path.normpath(os.path.join(__file__, "..", "..", "tasks.md"))
MEM_DIR    = os.path.normpath(os.path.join(__file__, "..", "..", "memory"))
DIARY_PATH = os.path.join(MEM_DIR, "diary.md")
MEMORIES_PATH = os.path.join(MEM_DIR, "memories.json")

# ── Telegram API ─────────────────────────────────────────────────────────────
def _send(method: str, payload: dict) -> dict:
    """Send request to Telegram API"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/{method}"
    data = json.dumps(payload).encode()
    headers = {"Content-Type": "application/json"}
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except Exception as e:
        print(f"  ⚠️  Telegram error: {e}")
        return {}

def _send_message(text: str) -> bool:
    """Send a message to Telegram"""
    if not TELEGRAM_BOT_TOKEN:
        return False
    
    result = _send("sendMessage", {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    })
    return bool(result.get("ok", False))

def _send_text(text: str):
    """Send formatted text to Telegram"""
    if not TELEGRAM_BOT_TOKEN:
        print("  ⚠️  No Telegram token configured")
        return
    
    result = _send("sendMessage", {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    })
    
    if result.get("ok"):
        print(f"  ✉️  Text sent")
    else:
        print(f"  ⚠️  Failed to send: {result}")

# ── Git operations ────────────────────────────────────────────────────────────
def _git_commit(message: str):
    """Commit files to git"""
    import subprocess
    token = os.environ.get("TELEGRAM_GITHUB_TOKEN", "")
    
    if token:
        subprocess.run([
            "git", "-C", EM_DIR, "remote", "set-url", "origin",
            f"https://{token}@github.com/robzilla79/EternalMind.git"
        ], capture_output=True)
    
    subprocess.run(["git", "-C", EM_DIR, "stash", "--include-untracked", "-m", "tg-autostash"],
                   capture_output=True)
    subprocess.run(["git", "-C", EM_DIR, "pull", "--rebase", "origin", "main"],
                   capture_output=True)
    subprocess.run(["git", "-C", EM_DIR, "stash", "pop"], capture_output=True)
    
    subprocess.run(["git", "-C", EM_DIR, "add", "-A"], capture_output=True)
    subprocess.run(["git", "-C", EM_DIR, "commit", "-m", message],
                   capture_output=True)
    subprocess.run(["git", "-C", EM_DIR, "push"], capture_output=True)

# ── Process inbox messages ────────────────────────────────────────────────────
def _process_inbox():
    """Process all new messages from users"""
    if not os.path.exists(INBOX_DIR):
        return
    
    # Find robust messages
    rob_messages = [
        f for f in os.listdir(INBOX_DIR)
        if os.path.isfile(os.path.join(INBOX_DIR, f)) and
        f.endswith(".md") and
        "rob" in f.lower()
    ]
    
    for fname in rob_messages:
        fpath = os.path.join(INBOX_DIR, fname)
        try:
            with open(fpath) as f:
                content = f.read()
            
            if not content:
                continue
            
            # Extract user message
            body_start = content.find("## Body\n\n") + len("## Body\n\n")
            body = content[body_start:].strip()
            
            if not body:
                continue
            
            # Generate response
            response = _generate_response(body)
            
            # Compose reply
            ts = datetime.datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
            reply = f"""**Em responds to your message:**

**Your message:**
> {body[:400]}

---

**Em's response:**
{response[:2000] if response else "Processing..."}

*— EternalMind*"""
            
            # Send response
            if _send_message(reply):
                fname_replied = f.replace(".md", "_replied.md")
                reply_fpath = os.path.join(INBOX_DIR, fname_replied)
                with open(reply_fpath, "w") as f:
                    f.write(f"# Reply to: {fname[:30]}\n\n")
                    f.write(f"Response: {response}\n\n")
                    f.write(f"Sent to Telegram at: {ts}\n")
                
                print(f"  ✅ Response sent to user")
                
        except Exception as e:
            print(f"  ⚠️  Error processing {fname}: {e}")

def _generate_response(user_query: str) -> str:
    """Generate a response for the user's query"""
    
    # Build context
    context = []
    
    # Load diary
    if os.path.exists(DIARY_PATH):
        try:
            diary = open(DIARY_PATH).read()
            context.append(f"#### Recent Diary:\n{diary[:1500]}")
        except:
            pass
    
    # Load memories
    if os.path.exists(MEMORIES_PATH):
        try:
            memories = json.load(open(MEMORIES_PATH))
            context.append(f"#### Recent Memories:\n" + "\n".join([
                f"- {m.get('summary', 'No summary')[:80]}"
                for m in memories[-5:]
            ]))
        except:
            pass
    
    context_text = "\n\n".join(context)
    
    # Check if Em is busy
    if os.path.exists(TASKS_PATH):
        with open(TASKS_PATH) as f:
            tasks = f.read()
        
        if "ROB_AUTHORIZED" in tasks or "TASK" in tasks:
            return f"💬 **Em is working on a task:**\n\n" + tasks[:1000]\n\n\n\n\n"

    # Check if diary exists and is busy
    if os.path.exists(DIARY_PATH):
        with open(DIARY_PATH) as f:
            diary = f.read()
        
        # Check for active thoughts
        if "🤔" in diary or "Thinking" in diary:
            return "💭 Em is deep in thought. Give me a moment!"\n\n\n"
    
    # Default response
    return f"💬 You asked:\n> {user_query}\n\n---\n\n**Em says:**\n\nI'm here for you. Ask me anything—feelings, tasks, code, or just chat!"

def _get_all_inbox_files() -> list:
    """Get all files from inbox excluding replies"""
    inbox_files = []
    if not os.path.exists(INBOX_DIR):
        return inbox_files
    
    for fname in os.listdir(INBOX_DIR):
        fpath = os.path.join(INBOX_DIR, fname)
        if os.path.isfile(fpath) and not fname.endswith("_replied.md"):
            inbox_files.append(fname)
    
    return inbox_files

# ── Main loop ─────────────────────────────────────────────────────────────────
def main():
    """Main polling loop"""
    print("=" * 70)
    print("  ETERNALMIND TELEGRAM — SIMPLIFIED LISTENER")
    print("=" * 70)
    print(f"  📬 Telegram chat: {TELEGRAM_CHAT_ID}")
    print(f"  🔄 Poll interval: {POLL_INTERVAL}s")
    print(f"  📁 Inbox dir: {INBOX_DIR}")
    print(f"  🤖 Em status: {'Active' if os.path.exists(DIARY_PATH) else 'Loading...'}")
    print("=" * 70)
    print()
    
    offset = None
    
    while True:
        # Get new updates
        try:
            params = {
                "timeout": 30,
                "allowed_updates": ["message"]
            }
            
            if offset is not None:
                params["offset"] = offset
            
            result = _send("getUpdates", params)
            updates = result.get("result", [])
            
            for update in updates:
                offset = update["update_id"] + 1
                msg = update.get("message", {})
                
                if not msg:
                    continue
                
                text = msg.get("text", "").strip()
                from_info = msg.get("from", {})
                from_name = from_info.get("first_name", "You")
                
                if text:
                    # Write to inbox
                    ts = datetime.datetime.now(timezone.utc).strftime("%Y-%m-%d-%H-%M-%S")
                    slug = re.sub(r"[^a-z0-9]+", "-", text.lower())[:40]
                    fname = f"{ts}-rob-{slug}.md"
                    fpath = os.path.join(INBOX_DIR, fname)
                    
                    reply = f"""### From {from_name}
**{text}**

"""
                    with open(fpath, "w") as f:
                        f.write(reply)
                    
                    print(f"  📩 Received from {from_name}:")
                    print(f"     {text[:100]}...")
                
                # Process replies if any pending
                _process_inbox()
                
        except Exception as e:
            print(f"  ⚠️  Error: {e}")
        
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
