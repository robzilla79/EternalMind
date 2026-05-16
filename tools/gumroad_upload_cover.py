#!/usr/bin/env python3
"""
gumroad_upload_cover.py
Uploads a cover image to an existing Gumroad product.
Usage: GUMROAD_ACCESS_TOKEN=... GUMROAD_PRODUCT_ID=gqthu python tools/gumroad_upload_cover.py
Image path defaults to public/assets/dev-prompt-pack-cover.png
"""
import os
import sys
import json
import urllib.request
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gumroad_products import load_token

PRODUCT_ID = os.environ.get("GUMROAD_PRODUCT_ID", "gqthu")
IMAGE_PATH = os.environ.get(
    "COVER_IMAGE_PATH",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "public", "assets", "dev-prompt-pack-cover.png")
)

if not os.path.exists(IMAGE_PATH):
    print(f"ERROR: Image not found at {IMAGE_PATH}", file=sys.stderr)
    sys.exit(1)

token = load_token()

# Multipart upload
boundary = "----FormBoundary7MA4YWxkTrZu0gW"
with open(IMAGE_PATH, "rb") as f:
    image_data = f.read()

filename = os.path.basename(IMAGE_PATH)
body = (
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
    f"Content-Type: image/png\r\n\r\n"
).encode() + image_data + f"\r\n--{boundary}--\r\n".encode()

url = f"https://api.gumroad.com/v2/products/{PRODUCT_ID}/covers"
req = urllib.request.Request(url, data=body, method="POST")
req.add_header("Authorization", f"Bearer {token}")
req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")

try:
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read().decode())
        print(f"Cover uploaded successfully.")
        print(json.dumps(result, indent=2))
except urllib.error.HTTPError as e:
    err = e.read().decode()
    print(f"ERROR {e.code}: {err}", file=sys.stderr)
    sys.exit(1)
