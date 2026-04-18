#!/usr/bin/env python
"""
Test script for Cloud-Em sync functionality.
Run this to verify the sync is set up correctly.
"""

import sys
import os

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 70)
print("  EternalMind Cloud-Em Sync — TEST")
print("=" * 70)
print()

# Check .env
env_path = os.path.join(os.getcwd(), ".env")
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            if line.startswith("PERPLEXITY_API_KEY") or line.startswith("CLOUD_SYNC_ENABLED"):
                print(f"  {line.strip()}")
else:
    print("  ⚠️  .env not found")
    print("  → Create .env with PERPLEXITY_API_KEY=CLOUD_SYNC_ENABLED=true")

# Check sync module
try:
    from tools.sync_cloud_em import sync_at_startup, sync_periodically
    print("  ✅ Sync module imported successfully")
except Exception as e:
    print(f"  ❌ Import failed: {e}")
    sys.exit(1)

# Check Perplexity bridge
try:
    from tools.em_bridge import send_to_cloud_em, estimate_cost
    print("  ✅ Bridge module imported successfully")
except Exception as e:
    print(f"  ❌ Bridge import failed: {e}")

# Show available functions
print()
print("  Available sync functions:")
print("    • sync_at_startup()   — Run on startup")
print("    • sync_periodically() — Run periodically")

# Check cloud replies directory
cloud_dir = os.path.join(os.getcwd(), "messages", "cloud_em_replies")
if os.path.exists(cloud_dir):
    print()
    print(f"  ✅ Cloud replies directory exists: {cloud_dir}")
    print(f"  🔎 Contents:")
    for f in sorted(os.listdir(cloud_dir))[-5:]:  # Last 5 files
        print(f"     └── {f}")
else:
    print()
    print(f"  ℹ️  Cloud replies dir not yet created: {cloud_dir}")

# Show config
print()
print("=" * 70)
print("  READY STATE:")
print("=" * 70)
print()
print("  To enable sync:")
print("    1. Edit .env")
print("    2. Add: PERPLEXITY_API_KEY=your_key")
print("    3. Set: CLOUD_SYNC_ENABLED=true")
print()
print("  Then run:")
print("    python local_em.py")
print()
print("  OR use:")
print("    python sync_and_start.bat")
print()
print("=" * 70)
