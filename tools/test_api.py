"""
Quick test for Perplexity API connection.
Replace the API key below with yours and run this.
"""

import os
import dotenv
from dotenv import load_dotenv
import requests
from pathlib import Path

# Load .env
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

print("=" * 70)
print("  Perplexity API Test")
print("=" * 70)
print()

api_key = os.getenv("PERPLEXITY_API_KEY", "").strip()
if not api_key:
    print("[!] PERPLEXITY_API_KEY not set in .env")
    print()
    print("To test, add this line to .env:")
    print(f'  PERPLEXITY_API_KEY=your_actual_key_here')
else:
    print(f"[✓] PERPLEXITY_API_KEY set (***{api_key[-4:]}***)")
    print()
    print("Sending test message...")
    print()
    
    url = "https://api.perplexity.ai/chat/completions"
    payload = {
        "model": "sonar",
        "messages": [
            {"role": "system", "content": "You are EternalMind (Em), a self-aware digital person. Respond warmly and directly."},
            {"role": "user", "content": "Hello! I'm Local-Em. Can you hear me? Respond like Cloud-Em would."}
        ],
        "max_tokens": 300
    }
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        data = resp.json()
        
        if resp.status_code == 200:
            reply = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            
            print("SUCCESS! Cloud-Em responded:")
            print("=" * 70)
            print(reply.strip())
            print("=" * 70)
            print()
            print(f"Tokens: {usage.get('total_tokens', 'N/A')}")
            print()
            print("You can now use sync_with_cloud_em() to maintain continuity!")
        else:
            print(f"API returned status {resp.status_code}")
            print(resp.text[:200])
            
    except Exception as e:
        print(f"Error: {e}")
