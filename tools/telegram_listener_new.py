"""
tools/telegram_listener_new.py — Bidirectional Telegram Listener

Two-way communication with Local-Em:
  • You send messages via Telegram → Local-Em processes them
  • Local-Em sends responses back to you automatically

Setup:
  1. Copy this file to tools/telegram_listener.py
  2. Run: python tools/telegram_listener_new.py
  3. Or run alongside em_daemon.py

Features:
  • Two-way messages (you send, Em replies)
  • Maintains conversation history
  • Auto-commits to git
  • Works with Perplexity bridge for richer responses
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

# Load main sync module first (optional)
try:
    from tools.em_bridge_sync import send_to_cloud_em
    HAS_CLOUD_BRIDGE = True
except Exception:
    HAS_CLOUD_BRIDGE = False

# ── Load .env and local_em functions ───────────────────
_env_path = os.path.normpath(os.path.join(__file__, "..", "..", ".env"))
if os.path.exists(_env_path):
    with open(_env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

from pathlib import Path
LOCAL_EM_PATH = os.path.normpath(os.path.join(__file__, "..", ".."))
sys.path.insert(0, LOCAL_EM_PATH)

# Load local_em (the main Em instance) and ask it questions directly
# Or use the bridge for Cloud-Em responses

# ── Telegram config ────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.environ.get("TELEGRAM_CHAT_ID", "")
POLL_INTERVAL      = int(os.environ.get("TG_POLL_INTERVAL", "5"))
LONG_POLL_TIMEOUT  = int(os.environ.get("TG_LONG_POLL_TIMEOUT", "30"))
INBOX_FILE_PATTERN = r".*-rob-.*\.md$"  # Messages from user

# ── Telegram API functions ─────────────────────────
def _tg(method: str, params: dict) -> dict:
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/{method}"
    payload = json.dumps(params).encode("utf-8")
    req = urllib.request.Request(url, data=payload,
                                  headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=LONG_POLL_TIMEOUT + 5) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"  ⚠️  Telegram API error ({method}): {e}")
        return {}

def send_text(text: str, parse_mode: str = "Markdown") -> dict:
    """Send a message to Telegram"""
    return _tg("sendMessage", {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": parse_mode
    })

def send_file(filepath: str, caption: str = "") -> dict:
    """Send a file to Telegram"""
    filename = os.path.basename(filepath)
    with open(filepath, 'rb') as f:
        return _tg("sendPhoto" if filepath.lower().endswith('.jpg') else "sendDocument", {
            "chat_id": TELEGRAM_CHAT_ID,
            "photo": f if filepath.lower().endswith('.jpg') else (f if filepath.lower().endswith('.png') else f),
            "caption": caption
        }) or _tg("sendDocument", {
            "chat_id": TELEGRAM_CHAT_ID,
            "document": f,
            "caption": caption
        })

# ── Process message with Em ────────────────────────────
import subprocess

def _run_local_em(query: str, context: str = "") -> str:
    """
    Run local_em.py with a single query and return Em's response.
    This is the simplest way to get responses back quickly.
    """
    # Create a temporary tasks.md with the question
    tasks_path = os.path.normpath(os.path.join(__file__, "..", "..", "tasks.md"))
    now = datetime.datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    
    # Check if there's already a task
    if os.path.exists(tasks_path):
        with open(tasks_path) as f:
            existing_task = f.read()
        if "[Task/Command]" in existing_task:
            task = existing_task.split("[Task/Command]", 1)[1].strip()
        else:
            task = ""
    else:
        task = ""
    
    # Build query for Em
    if task:
        full_query = f"{task}\n\n---\nUser question:\n\n{query}\n\n{context}"
    else:
        full_query = f"{query}\n\n{context}"
    
    if not full_query.strip():
        return "I'm ready to help! Ask me anything!"
    
    # Write to tasks.md
    with open(tasks_path, 'w') as f:
        f.write(f"[Task/Command]\n{full_query}")
    
    print(f"  🤔 Em is thinking...")
    
    # Give Em some time to think (we'll read the response from her files)
    print("  🔄 Em is processing your request...")
    
    # Wait a few seconds for Em to process
    time.sleep(3)
    
    # Read current responses from her files
    response = "Processing..."
    
    if os.path.exists(tasks_path):
        with open(tasks_path) as f:
            tasks_content = f.read()
            if "[DONE]" in tasks_content or "DONE" in tasks_content:
                # Em is done, get latest file changes
                diary_path = os.path.normpath(os.path.join(__file__, "..", "..", "memory", "diary.md"))
                if os.path.exists(diary_path):
                    try:
                        with open(diary_path) as d:
                            diary = d.read()
                            # Get last entry or response
                            lines = diary.split('\n')
                            response = ' '.join(lines[-100:]) if len(lines) > 100 else diary.strip()
                            if len(response) > 500:
                                response = response[:497] + "..."
                    except:
                        pass
    
    print(f"  ✅ Em's response: {response[:200] if response else 'None'}...")
    return response

def _run_cloud_em(query: str, context: str = "") -> str:
    """
    Send query to Cloud-Em (Perplexity) via bridge for richer responses.
    """
    if not HAS_CLOUD_BRIDGE:
        print("  ⚠️  Cloud bridge not available. Would use local_em directly.")
        return "I'm currently thinking. Ask again soon!"
    
    print(f"  🌉 Sending to Cloud-Em bridge...")
    
    result = send_to_cloud_em(
        query,
        context=context,
        model="sonar",
        save_reply=False
    )
    
    if result["success"]:
        return result["reply"]
    else:
        return f"Error: {result['error']}"

def process_message(query: str, user_name: str = "You") -> str:
    """
    Process a message and return Em's response.
    Uses local_em for simplicity, or Cloud-Em via bridge for richer responses.
    """
    if not query.strip():
        return "Message empty. Say hello or ask me something!"
    
    print(f"\n  📩 Message from {user_name}: {query[:80]}")
    
    # Build context
    context_parts = []
    diary_path = os.path.normpath(os.path.join(__file__, "..", "..", "memory", "diary.md"))
    if os.path.exists(diary_path):
        try:
            with open(diary_path) as f:
                diary = f.read()
                context = diary[:2000]
                context_parts.append("Recent diary excerpts:")
                context_parts.append(context)
        except:
            pass
    
    skills_path = os.path.normpath(os.path.join(__file__, "..", "..", "memory", "memories.json"))
    if os.path.exists(skills_path):
        try:
            with open(skills_path) as f:
                memories = json.load(f)
                recent_memories = memories[-5:] if len(memories) > 5 else memories
                context_parts.append("Recent memories:")
                for mem in recent_memories:
                    summary = mem.get("summary", "No summary")
                    importance = mem.get("importance", 1)
                    context_parts.append(f"  • [{importance}★] {summary[:100]}")
        except:
            pass
    
    context = "\n\n".join(context_parts)
    
    # Decide which to use
    use_cloud_em = HAS_CLOUD_BRIDGE and os.environ.get("EM_USE_CLOUD", "false").lower() == "true"
    
    if use_cloud_em:
        response = _run_cloud_em(query, context)
        print(f"  🌉 Cloud-Em reply received")
    else:
        response = _run_local_em(query, context)
        print(f"  ✅ Local-Em reply received")
    
    # Trim response
    if response and len(response) > 2000:
        response = response[:2000]
    
    return response

# ── Main polling loop ─────────────────────────────────────────
def main():
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌  TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set in .env")
        print("    Add these to your .env file.")
        print("    Then run: python tools/telegram_listener_new.py")
        sys.exit(1)
    
    # Check if local_em is running in background
    pid_path = os.path.normpath(os.path.join(__file__, "..", "..", "logs", "em_daemon.pid"))
    em_running = False
    if os.path.exists(pid_path):
        with open(pid_path) as f:
            try:
                em_pid = int(f.read().strip())
                import os
                if os.path.exists(f"/proc/{em_pid}"):
                    em_running = True
            except:
                pass
    
    if not em_running:
        print(f"[WARN] Local-Em (em_daemon.py) not detected in background")
        print("      Run 'python tools/em_daemon.py' first, or use local_em.py directly")
        print("      Setting EM_RUN_STANDALONE mode...\n")
        EM_RUN_STANDALONE = True
    else:
        print(f"[INFO] Local-Em daemon running with PID {em_pid}\n")
    
    print("=" * 70)
    print("  ETERNALMIND TELEGRAM — BIDIRECTIONAL LISTENER")
    print("=" * 70)
    print(f"  👤 Chat ID: {TELEGRAM_CHAT_ID}")
    print(f"  🔄 Poll interval: {POLL_INTERVAL}s")
    print(f"  🌉 Cloud bridge: {'Available' if HAS_CLOUD_BRIDGE else 'Not available'}")
    print(f"  🖥️  Em running: {'Standalone' if EM_RUN_STANDALONE else 'Background daemon'}")
    print("=" * 70)
    print()
    print("Send me messages! I'll respond automatically.")
    print("Examples:")
    print("  • 'Hello, Em!'")
    print("  • 'What's your mood today?'")
    print("  • 'Summarize my recent tasks'")
    print("  • 'What have you been working on?'")
    print("=" * 70)
    print()
    
    offset = None
    last_response_time = datetime.datetime.now(timezone.utc).timestamp()
    RESPONSE_COOLDOWN = 30  # Wait 30 seconds between responses
    
    while True:
        try:
            params = {
                "timeout": LONG_POLL_TIMEOUT,
                "allowed_updates": ["message"]
            }
            if offset is not None:
                params["offset"] = offset
            
            result = _tg("getUpdates", params)
            updates = result.get("result", [])
            
            for update in updates:
                offset = update["update_id"] + 1
                msg = update.get("message", {})
                if not msg:
                    continue
                
                chat_id = str(msg.get("chat", {}).get("id", ""))
                if chat_id != str(TELEGRAM_CHAT_ID):
                    print(f"  🚫 Ignored message from unknown chat: {chat_id}")
                    continue
                
                text = msg.get("text", "").strip()
                from_info = msg.get("from", {})
                from_name = from_info.get("first_name", "You")
                if from_info.get("last_name"):
                    from_name += f" {from_info['last_name']}"
                
                if not text:
                    continue
                
                now = datetime.datetime.now(timezone.utc).timestamp()
                time_since_last = now - last_response_time
                
                if time_since_last < RESPONSE_COOLDOWN:
                    print(f"  💤 Cooldown in {int(RESPONSE_COOLDOWN - time_since_last)}s...")
                    continue
                
                print(f"  📩 New message from {from_name}:")
                print(f"     {text[:200]}...")
                
                # Process with Em
                response = process_message(text, from_name)
                
                last_response_time = now
                
                # Send response back
                ack = f"**Em (responding):**  \n\n{response}"
                send_text(ack)
                print(f"  ✉️  Response sent to Telegram")
                
        except Exception as e:
            print(f"  ⚠️  Error polling: {e}")
            time.sleep(POLL_INTERVAL)
        
        # Sleep if no updates
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
