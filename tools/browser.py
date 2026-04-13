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
  - All actions are logged to diary
  - Screenshots saved to ~/em_screenshots/
  - Rob can review all browser activity via diary.md
"""

import os
import re
import datetime
from datetime import timezone

# ── SECURITY BLOCKLIST ──────────────────────────────────────────────────────
# Em will never navigate to these patterns
BLOCKLIST = [
    r'localhost:(?!8\d{3})',   # allow common dev ports 8xxx, block others
    r'127\.0\.0\.1',
    r'192\.168\.',
    r'10\.0\.',
    r'172\.(1[6-9]|2\d|3[01])\.',  # RFC1918
    r'file://',
    r'chrome://settings',
    r'chrome://extensions',
    r'about:',
]

SCREENSHOT_DIR = os.path.join(os.path.expanduser('~'), 'em_screenshots')
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

_browser = None
_page = None


def _get_page():
    """Lazy-init Playwright browser. Reuses existing session."""
    global _browser, _page
    if _page is not None:
        return _page
    try:
        from playwright.sync_api import sync_playwright
        pw = sync_playwright().start()
        _browser = pw.chromium.launch(
            headless=False,           # Rob can watch Em browse!
            args=['--start-maximized']
        )
        context = _browser.new_context(
            viewport={'width': 1280, 'height': 900},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        _page = context.new_page()
        return _page
    except ImportError:
        raise RuntimeError(
            'Playwright not installed. Run: pip install playwright && python -m playwright install chromium'
        )


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
    """Navigate to a URL. Returns page title."""
    if _is_blocked(url):
        return f'BLOCKED: {url} is on the security blocklist.'
    page = _get_page()
    _log_action('navigate', url)
    page.goto(url, wait_until='domcontentloaded', timeout=15000)
    title = page.title()
    return f'Navigated to: {url}\nTitle: {title}'


def click(selector: str) -> str:
    """Click an element by CSS selector or text."""
    page = _get_page()
    _log_action('click', selector)
    try:
        page.click(selector, timeout=5000)
        return f'Clicked: {selector}'
    except Exception as e:
        return f'Click failed on {selector}: {e}'


def type_text(selector: str, text: str) -> str:
    """Type text into an input field."""
    page = _get_page()
    _log_action('type', f'{selector} -> {text[:50]}')
    try:
        page.fill(selector, text)
        return f'Typed into {selector}: {text[:80]}'
    except Exception as e:
        return f'Type failed on {selector}: {e}'


def read_page() -> str:
    """Get the visible text content of the current page (up to 6k chars)."""
    page = _get_page()
    _log_action('read page')
    try:
        text = page.inner_text('body')
        return text[:6000]  # 6k chars — richer content, zero API cost
    except Exception as e:
        return f'Read failed: {e}'


def take_screenshot(name: str = None) -> str:
    """Take a screenshot. Saves to ~/em_screenshots/. Returns file path."""
    page = _get_page()
    ts = datetime.datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')
    fname = f'{name or "screenshot"}-{ts}.png'
    fpath = os.path.join(SCREENSHOT_DIR, fname)
    _log_action('screenshot', fpath)
    try:
        page.screenshot(path=fpath, full_page=False)
        return f'Screenshot saved: {fpath}'
    except Exception as e:
        return f'Screenshot failed: {e}'


def execute_js(script: str) -> str:
    """Execute JavaScript on the current page."""
    page = _get_page()
    _log_action('js', script[:80])
    try:
        result = page.evaluate(script)
        return f'JS result: {result}'
    except Exception as e:
        return f'JS failed: {e}'


def get_url() -> str:
    """Get the current URL."""
    if _page is None:
        return 'No browser session active.'
    return _page.url


def close_browser():
    """Close the browser session."""
    global _browser, _page
    if _browser:
        _browser.close()
        _browser = None
        _page = None
    return 'Browser closed.'


# ── RESPONSE PARSER ─────────────────────────────────────────────────────────

def execute_browser_commands(response_text: str) -> str:
    """
    Parse and execute BROWSER_* commands from Em's response.
    Returns a summary of all actions taken.
    """
    results = []

    nav_match = re.findall(r'BROWSER_NAV:\s*(https?://\S+)', response_text, re.IGNORECASE)
    for url in nav_match:
        results.append(navigate(url.strip()))

    click_matches = re.findall(r'BROWSER_CLICK:\s*(.+)', response_text, re.IGNORECASE)
    for sel in click_matches:
        results.append(click(sel.strip()))

    type_matches = re.findall(r'BROWSER_TYPE:\s*(.+?)\s*\|\s*(.+)', response_text, re.IGNORECASE)
    for sel, text in type_matches:
        results.append(type_text(sel.strip(), text.strip()))

    if re.search(r'BROWSER_READ:', response_text, re.IGNORECASE):
        results.append('--- Page content ---\n' + read_page())

    ss_matches = re.findall(r'BROWSER_SCREENSHOT:\s*(\S+)', response_text, re.IGNORECASE)
    for name in ss_matches:
        results.append(take_screenshot(name.strip()))

    js_matches = re.findall(r'BROWSER_JS:\s*(.+)', response_text, re.IGNORECASE)
    for script in js_matches:
        results.append(execute_js(script.strip()))

    if re.search(r'BROWSER_CLOSE:', response_text, re.IGNORECASE):
        results.append(close_browser())

    return '\n'.join(results) if results else ''
