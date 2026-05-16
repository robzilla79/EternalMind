#!/usr/bin/env python3
"""
perplexity_client.py

Centralized Perplexity API client for all Em tools.
One place to update if the endpoint, model, or auth ever changes.

Usage:
    from perplexity_client import ask_perplexity
    response = ask_perplexity(system="You are Em.", user="What should I write today?")

Endpoint: https://api.perplexity.ai/chat/completions (OpenAI-compatible)
Models: sonar (fast), sonar-pro (thorough)
Auth: Bearer PERPLEXITY_API_KEY
"""
import os
import json
import urllib.request
import urllib.error

PERPLEXITY_ENDPOINT = "https://api.perplexity.ai/chat/completions"
DEFAULT_MODEL = "sonar"


def ask_perplexity(
    system: str,
    user: str,
    model: str = DEFAULT_MODEL,
    max_tokens: int = 2048,
    temperature: float = 0.7,
    response_format: dict = None,
) -> str:
    """
    Send a prompt to Perplexity and return the response text.
    Raises RuntimeError on API failure.
    """
    api_key = os.environ.get("PERPLEXITY_API_KEY")
    if not api_key:
        raise RuntimeError("PERPLEXITY_API_KEY not set in environment.")

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    if response_format:
        payload["response_format"] = response_format

    body = json.dumps(payload).encode()
    req = urllib.request.Request(PERPLEXITY_ENDPOINT, data=body, method="POST")
    req.add_header("Authorization", f"Bearer {api_key}")
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json")

    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read().decode())
            return result["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Perplexity API error {e.code}: {e.read().decode()}")


def ask_perplexity_pro(system: str, user: str, **kwargs) -> str:
    """Convenience wrapper for sonar-pro when thoroughness matters."""
    return ask_perplexity(system=system, user=user, model="sonar-pro", **kwargs)
