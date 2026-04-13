"""
tools/summarize.py
Ask Local-Em (Ollama) to summarize long text before it blows her context window.
Usage: from tools.summarize import summarize
       short = summarize(long_text, instruction="focus on AI implications")
"""
import os
import json
import urllib.request
import urllib.error

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
MODEL = "em-local"

def summarize(text: str, instruction: str = "Summarize the key points concisely.", max_words: int = 150) -> str:
    """
    Ask Ollama to summarize text. Returns a short summary string.
    Falls back gracefully if Ollama is unavailable.
    """
    if len(text) < 500:
        return text  # Short enough already

    prompt = f"{instruction} Keep it under {max_words} words. Do not add commentary.\n\nTEXT:\n{text[:6000]}"

    payload = json.dumps({
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.3, "num_predict": 300}
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{OLLAMA_HOST}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("response", "").strip()
    except Exception as e:
        # Fallback: return first 500 chars with a note
        return text[:500] + f"\n[summarize failed: {e}]"

if __name__ == "__main__":
    import sys
    sample = sys.stdin.read() if not sys.stdin.isatty() else "Artificial intelligence is transforming industries at an unprecedented pace. From healthcare to finance, AI tools are being adopted widely. Large language models in particular have shown remarkable capabilities in reasoning, coding, and creative tasks. However, concerns about safety, bias, and job displacement remain significant. Researchers are working on alignment techniques to ensure AI systems behave as intended."
    print(summarize(sample))
