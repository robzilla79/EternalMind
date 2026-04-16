# Em's Tools

This directory contains tool modules that Local-Em can invoke during her heartbeat cycles.

## Available Tools

### `web_search.py`
Web search via API. Em uses it with `TOOL: web_search("query")` syntax.

### `clawhub_skills.py`
Searches clawhub.ai for skill URLs and installs a skill scaffold from the linked GitHub repo.

**Em syntax:**
```
TOOL: clawhub_search("redis")
TOOL: clawhub_install("https://www.clawhub.ai/skills/skill-name", "YES")
```

Install is blocked unless explicit `"YES"` approval is included.

### `browser.py`
Playwright-based browser automation. Em can navigate, click, type, read pages, and take screenshots.

**Em's browser syntax:**
```
BROWSER_NAV: https://example.com
BROWSER_CLICK: #selector or text
BROWSER_TYPE: #selector | text to type
BROWSER_READ:
BROWSER_SCREENSHOT: name
BROWSER_JS: javascript expression
BROWSER_CLOSE:
```

**Setup (one-time):**
```bash
pip install playwright
python -m playwright install chromium
```

**Security:** Em cannot navigate to local network addresses (192.168.x.x, 127.0.0.1) or
sensitive browser pages. All browser activity is logged to diary.md.
Screenshots are saved to `~/em_screenshots/`.

### `notify_rob.py`
Sends push/desktop notifications to Rob. Em uses `NOTIFY: message` syntax.
