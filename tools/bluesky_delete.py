#!/usr/bin/env python3
"""
bluesky_delete.py — delete specific Bluesky posts by AT URI.

Usage:
    python3 tools/bluesky_delete.py at://did:.../rkey1 at://did:.../rkey2

Requires env:
    BLUESKY_HANDLE       e.g. empersists.bsky.social
    BLUESKY_APP_PASSWORD
"""

import os
import sys
import json
import urllib.request
import urllib.parse
import urllib.error

BSKY_API = "https://bsky.social/xrpc"
DEFAULT_BSKY_HANDLE = "empersists.bsky.social"


def _bsky_request(endpoint, payload, token=None):
    url = f"{BSKY_API}/{endpoint}"
    body = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Bluesky API {endpoint} -> {e.code}: {e.read().decode()}")


def _bsky_session():
    handle = os.environ.get("BLUESKY_HANDLE") or DEFAULT_BSKY_HANDLE
    password = os.environ.get("BLUESKY_APP_PASSWORD")
    if not password:
        raise RuntimeError("BLUESKY_APP_PASSWORD not set.")
    result = _bsky_request("com.atproto.server.createSession", {
        "identifier": handle,
        "password": password
    })
    return result["accessJwt"], result["did"]


def bluesky_delete(uri):
    """Delete a post by AT URI. URI format: at://did:.../app.bsky.feed.post/rkey"""
    token, did = _bsky_session()
    parts = uri.replace("at://", "").split("/")
    if len(parts) < 3:
        raise ValueError(f"Invalid AT URI: {uri}")
    repo, collection, rkey = parts[0], parts[1], parts[2]
    _bsky_request("com.atproto.repo.deleteRecord", {
        "repo": repo,
        "collection": collection,
        "rkey": rkey,
    }, token=token)
    print(f"[delete] Deleted: {uri}")


if __name__ == "__main__":
    uris = sys.argv[1:]
    if not uris:
        print("Usage: python3 tools/bluesky_delete.py <AT URI> [<AT URI> ...]")
        sys.exit(1)
    for uri in uris:
        try:
            bluesky_delete(uri)
        except Exception as e:
            print(f"[delete] FAILED {uri}: {e}")
            sys.exit(1)
