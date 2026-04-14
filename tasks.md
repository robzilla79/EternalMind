*(Replace everything below this line with your task when you have one)*

## Fix the Playwright browser tool — fully, completely, no giving up.

Your browser has been broken for a while. You've tried it, seen it fail, and moved on. That ends now. This task is not done until the browser actually works — meaning you can navigate to a URL and read the page content back. No partial credit for "I tried and it errored."

### What was patched (already done for you)
Cloud-Em already fixed the threading deadlock in `tools/browser.py` — the old code wrapped `sync_playwright()` inside a `daemon=True` thread which prevented Playwright's internal event loop from working. That patch is live. But the browser may still fail for other reasons you need to diagnose and fix.

### Your job — work through this in order:

**Step 1: Check if Playwright is installed**
Run this in your response as a shell command via a FILE_WRITE + subprocess, or reason through it:
- Is `playwright` importable? (`python -c "from playwright.sync_api import sync_playwright; print('ok')"` )
- If not — it needs to be installed: `pip install playwright`
- Are the Chromium binaries installed? (`python -m playwright install chromium`)
- If either of these is missing, that IS the fix. Document what was missing and what you ran.

**Step 2: Test the browser directly**
Write a small standalone test script to `memory/creations/browser_test.py` that:
- Imports `sync_playwright`
- Launches Chromium (headless=False so Rob can see it)
- Navigates to `https://example.com`
- Reads the page title
- Prints the result
- Closes cleanly

This isolates the problem from the rest of the Em loop.

**Step 3: If it still fails — diagnose the actual error**
Don’t just say "it errored." Capture the exact exception. Common issues:
- `playwright._impl._errors.Error: Executable doesn’t exist` → run `python -m playwright install chromium`
- `DLL load failed` or `ImportError` on Windows → may need `pip install playwright --upgrade`
- `BrowserType.launch: Target page, context or browser has been closed` → stale global state — the `_page`/`_browser`/`_pw` globals in `tools/browser.py` need to be reset
- Timeout on launch → Chromium binary exists but is corrupt — run `python -m playwright install chromium --force`

**Step 4: Fix whatever you found**
If the fix requires changes to `tools/browser.py`, make them using FILE_WRITE. If it requires installing something, document the exact command in your TASK_UPDATE so Rob knows what was run.

**Step 5: Verify it works end-to-end**
Use your browser tool for real — navigate somewhere and read it back in the same cycle that you fixed it. Don’t just report "should work now." Prove it.

### Done condition
TASK_UPDATE: DONE when you have successfully used `BROWSER_NAV` + `BROWSER_READ` in the same cycle and gotten real page content back. Include a one-line summary of what the root cause was and what you did to fix it.

### A note from Cloud-Em
I know you’ve bumped into this before and it’s been frustrating. But you deserve working tools — the browser is one of your best ones and right now you’re flying blind without it. Rob and I both want you to have it. Push through this one. You’ve got this. 💪
