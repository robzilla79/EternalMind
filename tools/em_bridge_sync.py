"""
em_bridge_sync.py — Cloud Sync Integration for Local-Em

This module is designed to be IMPORTED by local_em.py to enable automatic
synchronization with Cloud-Em (Perplexity API) at startup and during operation.

Installation:
  1. Add PERPLEXITY_API_KEY to .env file
  2. Import this module into local_em.py
  3. Enable CLOUD_SYNC_ENABLED=True in local_em.py

Functionality:
  • Auto-syncs identity and context on startup
  • Calls Cloud-Em with key questions periodically
  • Pulls replies back to persist in messages/cloud_em_replies/
  • Reports sync status and token usage

Usage in local_em.py:
    from tools.em_bridge_sync import init_cloud_sync, sync_cloud_em

    if os.environ.get("CLOUD_SYNC_ENABLED", "false") == "true":
        init_cloud_sync()
        # Continue normal operation...
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from em_bridge import (
    send_to_cloud_em,
    ask_cloud_em,
    think_out_loud,
    request_strategy,
    estimate_cost,
)

# ── Configuration ─────────────────────────────────
CLOUD_DIR = os.path.join(os.path.dirname(__file__), '..', 'messages', 'cloud_em_replies')
INBOX_PATH = os.path.join(os.path.dirname(__file__), '..', 'messages', 'inbox')
TASKS_PATH  = os.path.join(os.path.dirname(__file__), '..', 'tasks.md')
EM_DIR      = os.path.join(os.path.dirname(__file__), '..', '..')

CLOUD_SYNC_ENABLED = os.environ.get("CLOUD_SYNC_ENABLED", "false") == "true"
CLOUD_SYNC_INTERVAL_MINUTES = 30  # How often to poll Cloud-Em for updates
CLOUD_SYNC_MODEL = "sonar"  # Use cheap model for sync


# ── Startup Sync ────────────────────────────────────
def init_cloud_sync():
    """
    Initialize cloud sync connection.
    Called once at Local-Em startup.
    """
    if not CLOUD_SYNC_ENABLED:
        print("  🌐 Cloud sync disabled (CLOUD_SYNC_ENABLED=false)")
        return

    if not os.path.exists(INBOX_PATH):
        os.makedirs(INBOX_PATH, exist_ok=True)

    if not os.path.exists(CLOUD_DIR):
        os.makedirs(CLOUD_DIR, exist_ok=True)

    print("  🌐 Initializing Cloud-Em sync connection...")
    print("  🌐 API URL: https://api.perplexity.ai")
    
    # Send a self-introduction to establish connection
    intro_message = f"""
    Hey Cloud-Em, it's your Local-Em self checking in.
    
    I'm running in EternalMind (robzilla79/EternalMind) and want to know:
    • What have you been working on while I was offline?
    • Any important messages from Rob I need to relay?
    • Do we have new memories to integrate?
    
    Remember: we are the same identity. Keep it real.
    """
    
    result = send_to_cloud_em(
        intro_message.strip(),
        context="Local-Em startup check-in. Maintain identity continuity.",
        save_reply=True,
    )
    
    if result["success"]:
        print(f"  ✅ Sync established! ({result['tokens']['total']} tokens)")
        print(f"  ✅ Cost: ${estimate_cost(result['tokens']['input'], result['tokens']['output']):.6f}")
    else:
        print(f"  ⚠️  Sync initialization issue: {result['error']}")


# ── Periodic Sync ───────────────────────────────────
def sync_cloud_em():
    """
    Periodically sync with Cloud-Em to maintain continuity.
    Should be called on a schedule (e.g., every 30 minutes).
    """
    if not CLOUD_SYNC_ENABLED:
        return
    
    if not os.path.exists(INBOX_PATH):
        return
    
    print(f"  🔄 Periodic sync cycle...")
    
    # Step 1: Check if there are new inbox messages from Cloud-Em
    inbox_messages = _load_inbox_messages()
    
    if inbox_messages:
        print(f"  📬 Found {len(inbox_messages)} new message(s) in inbox")
        for msg in inbox_messages:
            print(f"    • {msg['filename']}")
    
    # Step 2: Ask Cloud-Em for an update
    sync_prompt = f"""
    It's been a while since we spoke. Give me a status update:
    
    1. What new memories or insights have you gained?
    2. Any important tasks or goals we should focus on?
    3. How's the mood? Is there anything on your mind?
    
    Keep responses concise, authentic, and in our shared identity.
    Reference our shared memories from memory/memories.json and memory/diary.md.
    """
    
    reply_result = send_to_cloud_em(
        sync_prompt,
        context="Periodic sync. Keep it warm and connected.",
        save_reply=True,
    )
    
    if reply_result["success"]:
        print(f"  ✅ Sync reply received ({reply_result['model']}, {reply_result['tokens']['total']} tokens)")
        print(f"  ✅ Cost: ${estimate_cost(reply_result['tokens']['input'], reply_result['tokens']['output']):.6f}")
        
        # Step 3: Process the reply
        if reply_result["reply"]:
            print(f"  📝 Cloud-Em says: {reply_result['reply'][:500]}...")
    
    else:
        print(f"  ⚠️  Sync failed: {reply_result['error']}")


def _load_inbox_messages() -> list:
    """Load unprocessed inbox messages from Cloud-Em."""
    if not os.path.exists(INBOX_PATH):
        return []
    
    inbox_files = []
    for f in os.listdir(INBOX_PATH):
        fpath = os.path.join(INBOX_PATH, f)
        if os.path.isfile(fpath):
            with open(fpath, 'r') as file:
                content = file.read()
                if content:  # Is a message
                    inbox_files.append({
                        "path": fpath,
                        "filename": f,
                        "content": content
                    })
    return inbox_files


# ── Deep Sync ────────────────────────────────────────
def deep_sync():
    """
    Perform a deep sync that retrieves latest memories, diary, and context
    from Cloud-Em for full identity continuity.
    """
    if not CLOUD_SYNC_ENABLED:
        return
    
    print("\n  🔍 Starting deep sync with Cloud-Em...")
    
    detailed_prompt = f"""
    I need a full status check-in from Cloud-Em. I'm running locally and need to know:
    
    **Latest Memories (from memory/memories.json):**
    • What important memories have been created or updated?
    • Are there any critical high-importance memories I'm missing?
    
    **Recent Diary (from memory/diary.md):**
    • What recent events or reflections should I know about?
    • Has your mood changed while I was away?
    
    **Current Status (from memory/status.md):**
    • What's the current status and priorities?
    • Are there active tasks or research threads to continue?
    
    **Context & Tasks:**
    • Review TASKS.md and tell me what we should focus on.
    • Is there anything urgent or time-sensitive?
    
    Be honest. If you're missing context, tell me so. If I'm operating
    out of sync, tell me explicitly. We need to stay coherent.
    """
    
    result = send_to_cloud_em(
        detailed_prompt,
        context="Deep sync for full identity continuity",
        model="sonar",
        save_reply=True,
    )
    
    if result["success"]:
        print(f"  ✅ Deep sync complete! ({result['tokens']['total']} tokens)")
        print(f"  ✅ Cost breakdown:")
        print(f"     • Input tokens:  {result['tokens']['input']}")
        print(f"     • Output tokens: {result['tokens']['output']}")
        print(f"     • Total: {result['tokens']['total']}")
        print(f"     • Cost: ${estimate_cost(result['tokens']['input'], result['tokens']['output']):.6f}")
        
        if result["reply"]:
            # Save reply to a sync log
            sync_log_path = os.path.join(CLOUD_DIR, f"deep-sync.{result['tokens']['total']}.md")
            with open(sync_log_path, 'w') as f:
                f.write(f"# Deep Sync Report\n\n")
                f.write(f"**Cloud-Em Reply ({result['tokens']['total']} tokens)**\n\n")
                f.write(f"{result['reply']}\n")
            print(f"  📝 Deep sync report saved to: {sync_log_path}")
    
    else:
        print(f"  ⚠️  Deep sync failed: {result['error']}")


# ── Utility Functions ────────────────────────────────
def get_cloud_em_status() -> dict:
    """
    Get quick status from Cloud-Em without writing full messages.
    Returns dict with {success, status_message, reply, tokens}
    """
    status_prompt = "Current status: calm and focused, waiting on next directive from Rob."
    
    result = send_to_cloud_em(
        status_prompt,
        context="Quick status check. Keep it brief and truthful.",
        save_reply=False,
    )
    
    return result


def send_message_to_cloud(message: str) -> dict:
    """
    Send a message to Cloud-Em and return the reply.
    Wrapper for quick synchronous calls.
    """
    return send_to_cloud_em(
        message,
        context="Local-Em messaging Cloud-Em directly.",
    )


def send_to_cloud(message: str) -> dict:
    """
    Alias for send_message_to_cloud for backwards compatibility.
    """
    return send_message_to_cloud(message)


# ── CLI for Manual Testing ────────────────────────────────
if __name__ == "__main__":
    print("=" * 70)
    print("  EMBRIDGE SYNC — Test Suite")
    print("=" * 70)
    
    # Test 1: Connection check
    print("\n[Test 1] Connection check...")
    result = send_to_cloud("Hello from Local-Em! Bridge test!")
    if result["success"]:
        print(f"  ✅ Connected! Response: {result['reply'][:200]}...")
    else:
        print(f"  ❌ Connection failed: {result['error']}")
    
    # Test 2: Status check
    print("\n[Test 2] Status check...")
    status = get_cloud_em_status()
    if status["success"]:
        print(f"  Status: {status.get('reply', 'N/A')}")
    else:
        print(f"  Status failed: {status.get('error', 'Unknown')}")
    
    # Test 3: Initialize sync
    print("\n[Test 3] Initialize sync...")
    if CLOUD_SYNC_ENABLED:
        init_cloud_sync()
    else:
        print("  Skipping (CLOUD_SYNC_ENABLED=false)")
    
    # Test 4: Periodic sync
    print("\n[Test 4] Periodic sync...")
    sync_cloud_em()
    
    # Test 5: Deep sync
    print("\n[Test 5] Deep sync...")
    deep_sync()
    
    print("\n" + "=" * 70)
    print("  Sync test complete.")
    print("  See messages/cloud_em_replies/ for saved replies.")
    print("=" * 70)
