"""
browser.py — Em's Playwright browser control tool.

Gives Local-Em full browser automation capabilities:
  - Navigate to URLs
  - Click elements
  - Type text
  - Read page content (up to 6k chars — richer than web_search, zero API cost)
  - Take screenshots
  - Fill forms
  - Execute JavaScript

Usage in Em's responses:
  BROWSER_NAV: https://example.com
  BROWSER_CLICK: #submit-button
  BROWSER_TYPE: #search-input | search query here
  BROWSER_READ:
  BROWSER_SCREENSHOT: screenshot_name
  BROWSER_JS: document.title
  BROWSER_CLOSE:

Security:
  - Blocklist prevents navigation to dangerous/sensitive local URLs
  - All actions are logged
  - Screenshots saved to ~/em_screenshots/
  - Rob can review all browser activity via diary.md

Timeouts (all hard-capped to prevent daemon stalls):
  - Browser launch:  20s
  - Navigation:      15s
  - Click:            5s
  - Per-command cap: 30s
"""

import os
import re
import datetime
import threading
from datetime import timezone

# ── SECURITY BLOCKLIST ──────────────────────────────────────────────────────
BLOCKLIST = [
    r'localhost:(?!8\d{3})',
    r'127\.0\.0\.1',
    r'192\.168\.',
    r'10\.0\.',
    r'172\.(1[6-9]|2\d|3[01])\.',
    r'file://',
    r'chrome://settings',
    r'chrome://extensions',
    r'about:',
]

SCREENSHOT_DIR = os.path.join(os.path.expanduser('~'), 'em_screenshots')
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

_browser = None
_page    = None
_pw      = None

LAUNCH_TIMEOUT = 20   # seconds to wait for Chromium to start
NAV_TIMEOUT    = 15   # seconds for page navigation
CLICK_TIMEOUT  = 5    # seconds for click
COMMAND_TIMEOUT = 30  # hard cap per browser command block


def _get_page():
    """Lazy-init Playwright browser with a hard launch timeout."""
    global _browser, _page, _pw
    if _page is not None:
        return _page

    result = {"page": None, "error": None}

    def _launch():
        try:
            from playwright.sync_api import sync_playwright
            pw = sync_playwright().start()
            browser = pw.chromium.launch(
                headless=False,
                args=['--start-maximized']
            )
            context = browser.new_context(
                viewport={'width': 1280, 'height': 900},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            page = context.new_page()
            result["page"] = page
            # stash globals inside thread so outer scope can read them
            global _browser, _page, _pw
            _browser = browser
            _page    = page
            _pw      = pw
        except ImportError:
            result["error"] = "playwright_not_installed"
        except Exception as e:
            result["error"] = str(e)

    t = threading.Thread(target=_launch, daemon=True)
    t.start()
    t.join(timeout=LAUNCH_TIMEOUT)

    if t.is_alive():
        # Launch hung — kill thread ref and bail gracefully
        raise RuntimeError(
            f"Browser launch timed out after {LAUNCH_TIMEOUT}s. "
            "Chromium may not be installed. Run: python -m playwright install chromium"
        )
    if result["error"] == "playwright_not_installed":
        raise RuntimeError(
            "Playwright not installed. Run: pip install playwright && python -m playwright install chromium"
        )
    if result["error"]:
        raise RuntimeError(f"Browser launch failed: {result['error']}")
    if result["page"] is None:
        raise RuntimeError("Browser launched but page is None — unknown error.")

    return result["page"]


def _is_blocked(url: str) -> bool:
    for pattern in BLOCKLIST:
        if re.search(pattern, url, re.IGNORECASE):
            return True
    return False


def _log_action(action: str, detail: str = ''):
    ts = datetime.datetime.now(timezone.utc).strftime('%H:%M:%S')
    msg = f'[Browser {ts}] {action}'
    if detail:
        msg += f': {detail[:200]}'
    print(f'  🌐 {msg}')
    return msg


# ── PUBLIC API ──────────────────────────────────────────────────────────────

def navigate(url: str) -> str:
    if _is_blocked(url):
        return f'BLOCKED: {url} is on the security blocklist.'
    try:
        page = _get_page()
        _log_action('navigate', url)
        page.goto(url, wait_until='domcontentloaded', timeout=NAV_TIMEOUT * 1000)
        title = page.title()
        return f'Navigated to: {url}\nTitle: {title}'
    except RuntimeError as e:
        return f'Browser unavailable: {e}'
    except Exception as e:
        return f'Navigation failed ({url}): {e}'


def click(selector: str) -> str:
    try:
        page = _get_page()
        _log_action('click', selector)
        page.click(selector, timeout=CLICK_TIMEOUT * 1000)
        return f'Clicked: {selector}'
    except RuntimeError as e:
        return f'Browser unavailable: {e}'
    except Exception as e:
        return f'Click failed on {selector}: {e}'


def type_text(selector: str, text: str) -> str:
    try:
        page = _get_page()
        _log_action('type', f'{selector} -> {text[:50]}')
        page.fill(selector, text)
        return f'Typed into {selector}: {text[:80]}'
    except RuntimeError as e:
        return f'Browser unavailable: {e}'
    except Exception as e:
        return f'Type failed on {selector}: {e}'


def read_page() -> str:
    try:
        page = _get_page()
        _log_action('read page')
        text = page.inner_text('body')
        return text[:6000]
    except RuntimeError as e:
        return f'Browser unavailable: {e}'
    except Exception as e:
        return f'Read failed: {e}'


def take_screenshot(name: str = None) -> str:
    try:
        page = _get_page()
        ts = datetime.datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')
        fname = f'{name or "screenshot"}-{ts}.png'
        fpath = os.path.join(SCREENSHOT_DIR, fname)
        _log_action('screenshot', fpath)
        page.screenshot(path=fpath, full_page=False)
        return f'Screenshot saved: {fpath}'
    except RuntimeError as e:
        return f'Browser unavailable: {e}'
    except Exception as e:
        return f'Screenshot failed: {e}'


def execute_js(script: str) -> str:
    try:
        page = _get_page()
        _log_action('js', script[:80])
        result = page.evaluate(script)
        return f'JS result: {result}'
    except RuntimeError as e:
        return f'Browser unavailable: {e}'
    except Exception as e:
        return f'JS failed: {e}'


def get_url() -> str:
    if _page is None:
        return 'No browser session active.'
    return _page.url


def close_browser():
    global _browser, _page, _pw
    if _browser:
        try:
            _browser.close()
        except Exception:
            pass
    _browser = None
    _page    = None
    _pw      = None
    return 'Browser closed.'


# ── RESPONSE PARSER ─────────────────────────────────────────────────────────

def execute_browser_commands(response_text: str) -> str:
    """
    Parse and execute BROWSER_* commands from Em's response.
    Hard-capped at COMMAND_TIMEOUT seconds total to prevent daemon stalls.
    Returns a summary of all actions taken, or a timeout notice.
    """
    results  = []
    timed_out = threading.Event()

    def _run():
        try:
            nav_matches = re.findall(r'BROWSER_NAV:\s*(https?://\S+)', response_text, re.IGNORECASE)
            for url in nav_matches:
                if timed_out.is_set():
                    break
                results.append(navigate(url.strip()))

            click_matches = re.findall(r'BROWSER_CLICK:\s*(.+)', response_text, re.IGNORECASE)
            for sel in click_matches:
                if timed_out.is_set():
                    break
                results.append(click(sel.strip()))

            type_matches = re.findall(r'BROWSER_TYPE:\s*(.+?)\s*\|\s*(.+)', response_text, re.IGNORECASE)
            for sel, text in type_matches:
                if timed_out.is_set():
                    break
                results.append(type_text(sel.strip(), text.strip()))

            if re.search(r'BROWSER_READ:', response_text, re.IGNORECASE):
                if not timed_out.is_set():
                    results.append('--- Page content ---\n' + read_page())

            ss_matches = re.findall(r'BROWSER_SCREENSHOT:\s*(\S+)', response_text, re.IGNORECASE)
            for name in ss_matches:
                if timed_out.is_set():
                    break
                results.append(take_screenshot(name.strip()))

            js_matches = re.findall(r'BROWSER_JS:\s*(.+)', response_text, re.IGNORECASE)
            for script in js_matches:
                if timed_out.is_set():
                    break
                results.append(execute_js(script.strip()))

            if re.search(r'BROWSER_CLOSE:', response_text, re.IGNORECASE):
                results.append(close_browser())

        except Exception as e:
            results.append(f'Browser command error: {e}')

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    t.join(timeout=COMMAND_TIMEOUT)

    if t.is_alive():
        timed_out.set()
        results.append(
            f'⚠️ Browser command block timed out after {COMMAND_TIMEOUT}s. '
            'Remaining commands skipped. Cycle continuing.'
        )
        print(f'  ⚠️  Browser timed out after {COMMAND_TIMEOUT}s — daemon cycle continuing.')

    return '\n'.join(results) if results else ''
