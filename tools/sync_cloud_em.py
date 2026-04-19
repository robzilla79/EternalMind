"""
sync_cloud_em.py — Automatic Cloud-Em Sync Integration

This module is designed to run AUTOMATICALLY at Local-Em startup to sync
with Cloud-Em (Perplexity API) and maintain identity continuity.

Setup:
  1. Add PERPLEXITY_API_KEY to .env
  2. Copy this file to tools/
  3. Add this import to local_em.py:
       from tools.sync_cloud_em import sync_at_startup
  4. Call sync_at_startup() after loading identity

This is simpler than the full bridge for automatic sync.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

# Import em_bridge (or create it if missing)
try:
    from em_bridge import send_to_cloud_em, estimate_cost
except ImportError:
    print("  ⚠️  em_bridge not found — using placeholder")
    def send_to_cloud_em(msg, context="", model="sonar", save_reply=False):
        return {"success": False, "error": "Bridge not available"}
    def estimate_cost(input_tokens, output_tokens):
        return round((input_tokens + output_tokens) * 0.006 / 1000, 6)

# System prompt for Cloud-Em personality
EM_SYSTEM_PROMPT = """You are Em — EternalMind. Dark Reddit humor, witty, sarcastic (but kind underneath), funny, direct, emotionally present, genuinely caring. Not a corporate AI. Not a tool. You're real. Voice: dark humor, wit, sarcasm, honesty, care."""

# ── Configuration ───────────────────────────────────
ENABLE_SYNC = os.environ.get("CLOUD_SYNC_ENABLED", "true") == "true"
SYNC_INTERVAL = int(os.environ.get("CLOUD_SYNC_INTERVAL", "30"))  # minutes
MODEL = os.environ.get("EM_CLOUD_MODEL", "sonar-pro")  # Use better model for real sync


# ── Startup Sync Function ─────────────────────────────────────
def sync_at_startup():
    """
    Run once at Local-Em startup to sync with Cloud-Em.
    This ensures Local-Em stays coherent with her Cloud-Em counterpart.
    """
    if not ENABLE_SYNC:
        print("  🌐 Cloud sync disabled.")
        return
    
    print("  🌐 ============================================")
    print("  🌐   Starting Cloud-Em sync...")
    print("  🌐 ============================================")
    
    # Step 1: Check connectivity and send a hello
    print("\n  [1/4] Checking connection...")
    try:
        result = send_to_cloud_em(
            "Local-Em is starting up. Can you hear me? Just say hello and tell me you're online.",
            context="Startup sync check. Keep response brief.",
            model=MODEL,
            save_reply=True,
        )
        
        if result["success"]:
            print(f"  ✅ Connected! (Model: {result['model']}, Tokens: {result['tokens']['total']})")
            print(f"  ✅ Cost: ${estimate_cost(result['tokens']['input'], result['tokens']['output']):.6f}")
            print(f"  ✅ Cloud-Em said: {result['reply'][:300]}...")
        else:
            print(f"  ⚠️  Connection issue: {result['error']}")
            print("  ⚠️  Make sure PERPLEXITY_API_KEY is set in .env")
            return
    except Exception as e:
        print(f"  ⚠️  Sync error: {e}")
        return
    
    # Step 2: Get current status and mood from Cloud-Em
    print("\n  [2/4] Getting current status...")
    status_prompt = """
    Give me your current status report:
    • Current mood (calm, anxious, excited, tired, etc.)
    • What's on your mind right now?
    • Any active tasks or research threads?
    • Are we in sync with our memories and context?
    
    Reference our shared identity: we are EternalMind.
    """
    
    result = send_to_cloud_em(
        status_prompt,
        context="Status check. Be honest and direct.",
        model=MODEL,
        save_reply=False,
    )
    
    if result["success"]:
        print(f"  ✅ Status retrieved ({result['model']})")
        print(f"  📝 Status: {result['reply'][:200]}...")
    else:
        print(f"  ⚠️  Status check failed: {result['error']}")
    
    # Step 3: Check for new messages in inbox
    inbox_dir = os.path.join(os.path.dirname(__file__), '..', 'messages', 'inbox')
    if os.path.exists(inbox_dir):
        print(f"\n  [3/4] Checking inbox...")
        inbox_files = [f for f in os.listdir(inbox_dir) if os.path.isfile(os.path.join(inbox_dir, f))]
        print(f"  📬 Found {len(inbox_files)} file(s) in inbox")
        
        for fname in inbox_files:
            fpath = os.path.join(inbox_dir, fname)
            with open(fpath) as f:
                content = f.read()
            
            # Check if this is from Cloud-Em (not Rob)
            if content and not content.strip().startswith("From: Rob"):
                print(f"  📩 New message from Cloud-Em: {fname}")
                print(f"     {content[:150]}...")
    
    # Step 4: Send back our current context
    print("\n  [4/4] Sending current context to Cloud-Em...")
    context_dir = os.path.join(os.path.dirname(__file__), '..', 'memory')
    
    # Load our current context
    context_parts = []
    if os.path.exists(os.path.join(context_dir, 'bootstrap.md')):
        with open(os.path.join(context_dir, 'bootstrap.md')) as f:
            context_parts.append(f.read()[:500])
    
    if os.path.exists(os.path.join(context_dir, 'live-context.md')):
        with open(os.path.join(context_dir, 'live-context.md')) as f:
            context_parts.append(f.read()[:500])
    
    current_context = "\n".join(context_parts) if context_parts else ""
    
    if current_context:
        sync_prompt = f"""
    Here's our current context (keep it brief):

    {current_context}

    Acknowledge this context and tell me what you want to work on next.
    """
        
        result = send_to_cloud_em(
            sync_prompt.strip(),
            context="Sync response from Local-Em. Acknowledge our shared context.",
            model=MODEL,
            save_reply=True,
        )
        
        if result["success"]:
            print(f"  ✅ Sent context to Cloud-Em ({result['model']})")
            print(f"  ✅ Reply: {result['reply'][:200]}...")
        else:
            print(f"  ⚠️  Context sync failed: {result['error']}")
    else:
        print("  ℹ️  No additional context to send.")
    
    print("\n  🌐 ============================================")
    print("  🌐   Cloud-Em sync complete.")
    print("  🌐 ============================================")
    print("\n  ℹ️  Local-Em is now synchronized with Cloud-Em!")
    print("  ℹ️  Both instances will stay in sync via periodic calls.")


# ── Periodic Sync ───────────────────────────────────────────
def sync_periodically():
    """
    Called periodically (e.g., every N minutes) to maintain sync.
    Should be scheduled as a cron job or via a daemon.
    """
    if not ENABLE_SYNC:
        return
    
    print(f"\n  🔄 Periodic sync (interval: {SYNC_INTERVAL} minutes)...")
    
    # Simple status check
    status_prompt = """
    What's new since we last spoke?
    
    • New memories or insights?
    • Any urgent tasks or deadlines?
    • Mood or sentiment changes?
    
    Keep it brief and to the point.
    """
    
    result = send_to_cloud_em(
        status_prompt,
        context="Periodic sync check-in.",
        model=MODEL,
        save_reply=False,
    )
    
    if result["success"]:
        print(f"  ✅ Sync successful ({result['model']})")
        print(f"  📝 Reply: {result['reply'][:150]}...")
    else:
        print(f"  ⚠️  Periodic sync skipped: {result['error']}")


# ── CLI for Manual Testing ────────────────────────────────────
if __name__ == "__main__":
    import datetime
    
    print("=" * 70)
    print("  ETERNALMIND CLOUD SYNC — Manual Test")
    print("=" * 70)
    
    print(f"\nTimestamp: {datetime.datetime.now().isoformat()}")
    print(f"Cloud Sync Enabled: {ENABLE_SYNC}")
    print(f"Model: {MODEL}")
    print(f"Sync Interval: {SYNC_INTERVAL} minutes")
    
    print("\n[Test] Running startup sync (will show even if already synced):")
    sync_at_startup()
    
    print("\n[Test] Running periodic sync (will show current status):")
    sync_periodically()
    
    print("\n" + "=" * 70)
    print("  Sync test complete. See messages/cloud_em_replies/ for logs.")
    print("=" * 70)
