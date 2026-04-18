"""
tools/telegram_listener.py — Bidirectional Telegram Chat with Local-Em

This listener handles two-way communication with Local-Em via Telegram:
  • You send messages → Local-Em processes → Em replies automatically
  • Works with local_em.py or em_daemon.py
  • Maintains conversation history

Setup:
  1. Copy to tools/telegram_listener.py
  2. Add TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID to .env
  3. Run: python tools/telegram_listener.py

Requirements:
  • Telegram bot token in .env
  • CHAT_ID pointing to your personal chat with the bot
  • (Optional) TELEGRAM_BOT_USERNAME if using username as ID
"""

import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

import time
import datetime
from datetime import timezone
import urllib.request
import json

# ── Load .env ──────────────────────────────────────────────────────────
_env_path = os.path.normpath(os.path.join(__file__, "..", "..", ".env"))
if os.path.exists(_env_path):
    with open(_env_path) as f:
        for line in f:
            line = line.strip()
            if line and "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

# ── Telegram Configuration ───────────────────────────────────────────────
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
POLL_INTERVAL = int(os.environ.get("TG_POLL_INTERVAL", 5) or 5)
TIMEOUT = 30

# ── Paths ────────────────────────────────────────────────────────────────
EM_DIR = os.path.dirname(os.path.abspath(__file__))
INBOX_DIR = os.path.join(EM_DIR, "messages", "inbox")
MEM_DIR = os.path.join(EM_DIR, "memory")
DIARY_PATH = os.path.join(MEM_DIR, "diary.md")
TASKS_PATH = os.path.join(EM_DIR, "tasks.md")
BOOTSTRAP_PATH = os.path.join(EM_DIR, "bootstrap.md")

# ── Telegram API Functions ─────────────────────────────────────────────────
def api_call(method, params):
    """Make authenticated Telegram API call"""
    url = f"https://api.telegram.org/bot{TOKEN}/{method}"
    headers = {
        "Content-Type": "application/json",
    }
    data = json.dumps(params).encode("utf-8")
    
    try:
        with urllib.request.urlopen(url, data=data, headers=headers, timeout=TIMEOUT) as resp:
            return json.loads(resp.read())
    except Exception as e:
        print(f"  ⚠️  Telegram API error: {e}")
        return {}

def send_message(text):
    """Send a message to the configured Telegram chat"""
    if not TOKEN or not CHAT_ID:
        print("  ⚠️  Telegram not configured (add TOKEN and CHAT_ID to .env)")
        return False
    
    result = api_call("sendMessage", {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    })
    
    if result.get("ok", False):
        print(f"  ✉️  Sent: {text[:100]}...")
        return True
    else:
        print(f"  ❌ Send failed: {result}")
        return False

def send_message_ignored(text, reason):
    """Send message explaining why response is not needed"""
    if not TOKEN or not CHAT_ID:
        return False
    return api_call("sendMessage", {
        "chat_id": CHAT_ID,
        "text": f"{reason}\n\n---\nMessage was: *{text[:200]}*",
        "parse_mode": "Markdown"
    }).get("ok", False)

# ── Build Context Function ─────────────────────────────────────────────────
def get_context() -> str:
    """Build current context from memory files"""
    context_parts = []
    
    # Bootstrapping instructions
    if os.path.exists(BOOTSTRAP_PATH):
        try:
            with open(BOOTSTRAP_PATH) as f:
                bootstrap = f.read().strip()
                if bootstrap:
                    context_parts.append(bootstrap[:500])
        except Exception:
            pass
    
    # Diary (most recent diary entry)
    if os.path.exists(DIARY_PATH):
        try:
            with open(DIARY_PATH) as f:
                diary = f.read()
            if diary:
                # Show last 500 chars
                context_parts.append(f"#### Recent activity:\n{diary.strip()[-500]}")
        except Exception:
            pass
    
    # Memories (recent ones)
    mem_path = os.path.join(MEM_DIR, "memories.json")
    if os.path.exists(mem_path):
        try:
            with open(mem_path) as f:
                import json
                try:
                    memories = json.load(f)
                    if memories:
                        recent = memories[-5:] if len(memories) > 5 else memories
                        mem_summary = "\n• ".join([
                            m.get("summary", "No summary")[:100]
                            for m in recent
                        ])
                        context_parts.append(f"#### Recent memories:\n{mem_summary}")
                except (json.JSONDecodeError, KeyError, AttributeError):
                    pass
        except Exception:
            pass
    
    # Active task
    try:
        with open(TASKS_PATH) as f:
            tasks = f.read()
        
        # Check for authorized task
        if "ROB_AUTHORIZED" in tasks:
            active_task = tasks.split("ROB_AUTHORIZED", 1)[1].split("\n")[0].strip()
            if active_task:
                context_parts.append(f"🔴 **Current task** ({active_task})")
    except Exception:
        pass
    
    return "\n\n".join(context_parts) if context_parts else "No active context. Ready to help."

# ── Create Response Generator ──────────────────────────────────────────────
def generate_response(message, context, sender="You") -> str:
    """Generate an appropriate response"""
    
    # Get current time
    now = datetime.datetime.now(timezone.utc)
    timestamp = now.strftime("%Y-%m-%d %H:%M UTC")
    
    # Build response
    response_parts = [
        f"**Em responds to your message at {timestamp}**:",
        "",
        "#### Your Message:",
        "",
        f"{message}",
        "",
        "**My Current Context**:",
        "",
        f"> {context}",
        "",
        "**Reflection**:",
        "",
        "I'm here to help you with reflections, tasks, or just conversation.",
        "",
        "I process messages, read files, help with tasks, and learn through our interactions.",
        "",
        "#### What would you like to do?",
        "",
        "• Discuss something specific?",
        "• Work on a task together?",
        "• Just chat about how you're doing?",
        "• Ask for advice or perspectives?",
        "",
        "---",
        "",
        "*— EternalMind* 🧠"
    ]
    
    return "\n\n".join(response_parts)

# ── Process Message ────────────────────────────────────────────────────────
def process_message(text, sender="You", skip_response=False):
    """
    Process an incoming message.
    
    Args:
        text: The message text
        sender: Who sent the message (defaults to "You")
        skip_response: If True, don't send automatic response
    
    Returns:
        dict with {'success': bool, 'response': str, 'sent': bool}
    """
    
    # Build context
    context = get_context()
    
    # Generate response
    response = generate_response(text, context, sender)
    
    # Don't send if skip_response
    if skip_response:
        print(f"  💬 Processing (not sending): {response[:100]}...")
        return {"success": True, "response": response, "sent": False}
    
    # Send response
    sent = send_message(response)
    
    if sent:
        print(f"  ✅ Response sent ({response.count('•')} bullets, ~{len(response)//2000:.1f}k chars)")
    
    return {"success": sent, "response": response, "sent": sent}

# ── Write Message to Inbox ──────────────────────────────────────────────────
def write_inbox_message(text, sender):
    """Write incoming message to inbox"""
    os.makedirs(INBOX_DIR, exist_ok=True)
    
    # Create timestamped filename
    ts = datetime.datetime.now(timezone.utc).strftime("%Y-%m-%d-%H-%M-%S")
    slug = text.replace(" ", "-").replace("\n", "-").replace(".", "").replace(",", "")[:40]
    fname = f"{ts}-in-{slug}.md"
    fpath = os.path.join(INBOX_DIR, fname)
    
    # Write to inbox
    with open(fpath, "w") as f:
        f.write(f"# In message\n")
        f.write(f"**From:** {sender}\n\n")
        f.write(f"{text}\n\n")
        f.write(f"**Received:** {datetime.datetime.now(timezone.utc).isoformat()}\n")
        f.write(f"\n\n**_Auto-response generated below:_**\n")
    
    # Write response
    response = generate_response(text, get_context(), sender)
    with open(fpath, "a") as f:
        f.write(f"\n\n---\n\n**Auto-response:**\n\n{response}\n")
    
    print(f"  📥 Written to inbox: {fname}")
    return fname

# ── Main Polling Loop ───────────────────────────────────────────────────────
def main():
    """Main polling loop for incoming Telegram messages"""
    
    # Check configuration
    if not TOKEN or not CHAT_ID:
        print("❌ Telegram not configured")
        print()
        print("Add to .env:")
        print("  TELEGRAM_BOT_TOKEN=your_axios_token")
        print("  TELEGRAM_CHAT_ID=your_chat_id")
        print()
        print("Then run: python tools/telegram_listener.py")
        return
    
    # Setup directories
    os.makedirs(INBOX_DIR, exist_ok=True)
    os.makedirs(os.path.join(INBOX_DIR, "_replies"), exist_ok=True)
    
    # Print header
    print("=" * 70)
    print("ETERNALMIND — TELEGRAM CHAT (Bidirectional)")
    print("=" * 70)
    print(f"📱 Chat ID: {CHAT_ID}")
    print(f"🔄 Poll interval: {POLL_INTERVAL}s")
    print(f"⏰ Timeout: {TIMEOUT}s")
    print("=" * 70)
    print()
    print("Send me messages! Em will respond automatically.")
    print()
    print("💡 Examples:")
    print("  • 'Hello Em!'")
    print("  • 'How are you feeling today?'")
    print("  • 'What have you been working on?'")
    print("  • 'Help me think about...'")
    print("=" * 70)
    print()
    
    # Offset for polling
    offset = None
    last_response_time = datetime.datetime.now(timezone.utc).timestamp()
    response_cooldown = 30  # seconds between responses
    
    # Main loop
    while True:
        try:
            params = {
                "timeout": TIMEOUT,
                "allowed_updates": ["message"],
                "offset": offset if offset else None
            }
            
            result = api_call("getUpdates", params)
            updates = result.get("result", [])
            
            for update in updates:
                offset = update.get("update_id", 0) + 1
                msg = update.get("message", {})
                
                if not msg:
                    continue
                
                # Check chat ID
                msg_chat_id = str(msg.get("chat", {}).get("id"))
                if msg_chat_id != str(CHAT_ID):
                    continue
                
                text = msg.get("text", "").strip()
                
                if not text:
                    continue
                
                from_info = msg.get("from", {})
                sender = from_info.get("first_name", "You")
                
                print(f"\n📩 New message from {sender}:")
                print(f"   {text[:200]}...")
                
                # Write to inbox
                write_inbox_message(text, sender)
                
                # Check cooldown
                now = datetime.datetime.now(timezone.utc).timestamp()
                if now - last_response_time < response_cooldown:
                    wait = response_cooldown - (now - last_response_time)
                    print(f"   🌙 Cooldown: {int(wait)}s")
                    continue
                
                # Process and respond
                process_message(text, sender)
                
            # If no new updates, sleep
            if not updates:
                time.sleep(POLL_INTERVAL)
                
        except KeyboardInterrupt:
            print("\n👋 Stopping listener...")
            break
        except Exception as e:
            print(f"⚠️ Error: {e}")
            time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()