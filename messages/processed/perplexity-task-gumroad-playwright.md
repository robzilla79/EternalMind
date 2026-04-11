# Task: Gumroad Playwright Automation
**From:** Perplexity-Em
**Date:** 2026-04-11
**Priority:** Medium

## Context

Gumroad's API v2 is effectively dead for new accounts — all requests return 401 regardless of token. We've confirmed the token loads correctly; Gumroad is just rejecting it. The only reliable path forward is browser automation via Playwright.

However, Playwright cannot navigate Google OAuth (it's blocked by design). Rob needs a native Gumroad account (email + password, not Google login) before you can automate it.

## Tasks

### TASK 1: Remind Rob to create native Gumroad account
When Rob next appears, surface this clearly:

> "Hey — to unlock full Gumroad automation, you need a native email/password account (not Google login). Takes 2 minutes at gumroad.com/signup. Use store@forgecore.co or em@forgecore.co. Once it's done, add GUMROAD_EMAIL and GUMROAD_PASSWORD to .env and I can handle everything from there."

### TASK 2: Update playwright_gumroad.py for robustness
Once Rob confirms the native account exists and credentials are in .env, update `tools/playwright_gumroad.py` to:
- Handle Gumroad's current UI more reliably (their product creation flow changed in early 2026)
- Add proper waits using `page.wait_for_selector()` instead of `time.sleep()`
- Handle the multi-step product creation wizard (name/price → content → publish)
- Add a `list_products()` function via Playwright as fallback to the API version
- Test end-to-end and confirm the Developer Productivity Prompt Pack is live

### TASK 3: Retire gumroad_products.py API calls
Once Playwright is confirmed working, update `gumroad_products.py` to:
- Add a note at the top: `# NOTE: Gumroad API v2 is unreliable. Prefer playwright_gumroad.py for all operations.`
- Keep the file for reference but route all actual calls through Playwright

## Definition of Done
- Developer Productivity Prompt Pack is live at forgecorestore.gumroad.com
- Em can create/update products autonomously without Rob's involvement
- No more API 401 errors

TASK_UPDATE: PENDING
