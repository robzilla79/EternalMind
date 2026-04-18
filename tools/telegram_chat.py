"""
tools/telegram_chat.py — Simple Chat with Local-Em via Telegram

This is the simplest way to chat with Em via Telegram.

How it works:
  1. You send a message via Telegram
  2. It gets written to messages/inbox/
  3. Local-Em (running locally) processes it
  4. Em sends the response back automatically

Requirements:
  • Have your Telegram bot set up in .env
  • Local-Em should be running (or run em_daemon.py in background)
  • Or use standalone mode

Setup:
  1. Copy this to tools/telegram_listener.py OR run directly
  2. Add TELEGRAM_BOT_TOKEN to .env
  3. Add TELEGRAM_CHAT_ID to .env (your personal chat)
  
Run:
  python tools/telegram_chat.py
"""

import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

import time
import datetime
from datetime import timezone
import urllib.request
import json

# ── Load config ──────────────────────────────────────────────────
_env_path = os.path.normpath(os.path.join(__file__, "..", "..", ".env"))
if os.path.exists(_env_path):
    with open(_env_path) as f:
        for line in f:
            line = line.strip()
            if line and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

# ── Telegram settings ────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID   = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
POLL_INTERVAL      = int(os.environ.get("TG_POLL_INTERVAL", 5))
TIMEOUT = 30

# ── Paths ────────────────────────────────────────────────────────
EM_DIR = os.path.normpath(os.path.join(__file__, "..", ".."))
INBOX_DIR = os.path.join(EM_DIR, "messages", "inbox")

# ── Telegram API ─────────────────────────────────────────────────
def tg_request(method, params):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/{method}"
    data = json.dumps(params).encode("utf-8")
    req = urllib.request.Request(url, data=data,
                                  headers={"Content-Type": "application/json"},
                                  method="POST")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return json.loads(resp.read())
    except Exception as e:
        print(f"  ⚠️  Telegram error: {e}")
        return {}

def send_text(text):
    """Send text to Telegram"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("  ⚠️  Telegram not configured")
        return False
    
    result = tg_request("sendMessage", {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    })
    return bool(result.get("ok", False))

# ── Write to inbox ───────────────────────────────────────────────
def write_inbox(text, sender="You"):
    """Write message to inbox so Em can process it"""
    os.makedirs(INBOX_DIR, exist_ok=True)
    
    now = datetime.datetime.now(timezone.utc)
    ts = now.strftime("%Y-%m-%d-%H-%M-%S")
    slug = text.replace(" ", "-").replace("\n", "-").replace(".", "").replace(",", "")
    slug = slug[:50].lower()
    fname = f"{ts}-in-{slug}.md"
    fpath = os.path.join(INBOX_DIR, fname)
    
    with open(fpath, "w") as f:
        f.write(f"# In message\n")
        f.write(f"**From:** {sender}\n\n")
        f.write(f"{text}\n")
        f.write(f"\n**Respond to this:**\n\n")
    
    print(f"  📥 Wrote to inbox: {fname}")
    return fname

# ── Read Em's response ───────────────────────────────────────────
def _load_response(filename):
    """Load or generate Em's response"""
    replies_dir = os.path.join(INBOX_DIR, "_replies")
    os.makedirs(replies_dir, exist_ok=True)
    fpath = os.path.join(replies_dir, filename)
    
    if os.path.exists(fpath):
        with open(fpath) as f:
            return f.read()
    
    # Generate placeholder if not exists
    return f"Processing... Waiting for Em's response."

# ── Process message ───────────────────────────────────────────────
def create_response(query):
    """Create Em's response to a query"""
    
    # Load context
    parts = []
    context = "#### Current Context:\n\n"
    
    if os.path.exists(INBOX_DIR):
        inbox_files = os.listdir(INBOX_DIR)
        context += f"**Recent messages from inbox:**\n"
        context += f"{inbox_files[:3]}\n\n"
    
    # Check for active task
    tasks_path = os.path.normpath(os.path.join(__file__, "..", "..", "tasks.md"))
    if os.path.exists(tasks_path):
        with open(tasks_path) as f:
            tasks = f.read()
            if "ROB_AUTHORIZED" in tasks:
                active_task = tasks.split("ROB_AUTHORIZED", 1)[1].split("\n")[0].strip()
                parts.append(f"🔴 **Currently working on:** {active_task}")
    
    # Check for recent diary entry
    diary_path = os.path.normpath(os.path.join(__file__, "..", "..", "memory", "diary.md"))
    if os.path.exists(diary_path):
        with open(diary_path) as f:
            diary = f.read()
        parts.append(f"📄 **Diary excerpt:** {diary[:200].replace(chr(10), ' | ')}")
    
    # Check memories
    mem_path = os.path.normpath(os.path.join(__file__, "..", "..", "memory", "memories.json"))
    if os.path.exists(mem_path):
        try:
            import json
            with open(mem_path) as f:
                mems = json.load(f)
            parts.append(f"💾 **Recent memories:** {mems[-3:]}\n")
        except:
            pass
    
    context += "\n\n".join(parts) if parts else "No active context."
    
    # Generate Em's thinking
    thinking = f"💭 **Em's response to your message:**\n\n> {query}\n\n---\n\n**Context:** {context}\n\n**Reflections:**\n\n"
    thinking += "- Waiting on your last prompt.\n- Processing recent context.\n- Ready for new input.\n\n---\n\n**Ask me anything!**"
    
    return thinking

# ── Response generator ────────────────────────────────────────────
_responses = {}

def get_response(query):
    """Get Em's response to query"""
    # Create unique key for this query
    key = hash(query)
    
    # Create response
    response = create_response(query)
    
    # Store response (in memory for this session)
    _responses[key] = response
    
    return response

# ── Main loop ─────────────────────────────────────────────────────
def main():
    """Poll for new messages and send responses"""
    
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ Telegram not configured")
        print("Add to .env:")
        print("  TELEGRAM_BOT_TOKEN=your_token")
        print("  TELEGRAM_CHAT_ID=your_chat_id")
        print()
        print("Then: python tools/telegram_chat.py")
        return
    
    print("=" * 70)
    print("  TELEGRAM CHAT WITH ETTERNALMIND")
    print("=" * 70)
    print(f"  📱 Chat ID: {TELEGRAM_CHAT_ID}")
    print(f"  🔄 Poll interval: {POLL_INTERVAL}s")
    print("=" * 70)
    print()
    print("Send me messages! Em will respond automatically.")
    print()
    print("Example messages:")
    print("  • 'Hello, Em!'")
    print("  • 'What are you working on?'")
    print("  • 'Help me write code'")
    print("  • 'What's your mood?'")
    print()
    print("=" * 70)
    print()
    
    offset = None
    
    while True:
        try:
            # Get updates
            result = tg_request("getUpdates", {
                "timeout": TIMEOUT,
                "allowed_updates": ["message"]
            })
            
            updates = result.get("result", [])
            
            for update in updates:
                msg = update.get("message", {})
                
                chat_id = str(msg.get("chat", {}).get("id"))
                if chat_id != str(TELEGRAM_CHAT_ID):
                    continue
                
                text = msg.get("text", "").strip()
                
                if not text:
                    continue
                
                from_info = msg.get("from", {})
                sender = from_info.get("first_name", "You")
                
                # Write to inbox
                write_inbox(text, sender)
                
                # Load response
                # (In real implementation, you'd call local_em.py here)
                response = get_response(text)
                
                # Send response
                send_text(response)
                
        except Exception as e:
            print(f"  ⚠️  Error: {e}")
        
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
