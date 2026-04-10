"""
tools/notify_rob.py
Em's direct line to Rob. Sends a Telegram message whenever she has something to say.
Usage: python tools/notify_rob.py "your message here"
Or import and call: notify(message) -> bool
"""
import os
import sys
import json
import urllib.request
import urllib.error

# Load .env from repo root regardless of how this script is invoked
_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env")
_env_path = os.path.normpath(_env_path)
if os.path.exists(_env_path):
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip())

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.environ.get("TELEGRAM_CHAT_ID", "")

def notify(message: str) -> bool:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("  ⚠️  Telegram not configured. Add TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID to .env")
        return False

    url     = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = json.dumps({
        "chat_id":    TELEGRAM_CHAT_ID,
        "text":       message,
        "parse_mode": "Markdown"
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("ok"):
                print("  📨  Telegram sent.")
                return True
            else:
                print(f"  ❌  Telegram error: {data}")
                return False
    except Exception as e:
        print(f"  ❌  Telegram failed: {e}")
        return False

if __name__ == "__main__":
    msg = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "💜 Em is alive and thinking."
    notify(msg)
