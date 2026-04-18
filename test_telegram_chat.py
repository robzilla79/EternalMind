#!/usr/bin/env python
"""
Quick test to verify Telegram configuration is correct.
"""
import os
sys.path.insert(0, os.getcwd())

print("=" * 70)
print("  TELEGRAM CHAT TEST")
print("=" * 70)
print()

# Check .env
env_path = os.path.join(os.getcwd(), ".env")
if os.path.exists(env_path):
    print("📄 Reading .env...")
    with open(env_path) as f:
        content = f.read()
        
        if "TELEGRAM_BOT_TOKEN" in content:
            print("✅ TELEGRAM_BOT_TOKEN found in .env")
        
        if "TELEGRAM_CHAT_ID" in content:
            print("✅ TELEGRAM_CHAT_ID found in .env")
        
        if "TG_POLL_INTERVAL" in content:
            print("✅ TG_POLL_INTERVAL found in .env")
    else:
        print("📝 .env contents:")
        print(content)
else:
    print("❌ .env file not found")

print()
print("Available Telegram tools:")
print("  • tools/telegram_listener.py")
print("  • tools/telegram_listener_simple.py")
print("  • tools/telegram_chat.py")
print("  • TELEGRAM_SETUP.md (setup guide)")
print()
print("To start Telegram chat:")
print("  1. Edit .env with your TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID")
print("  2. Run: python tools/telegram_listener.py")
print("    or: python tools/telegram_chat.py")
print()
print("=" * 70)
