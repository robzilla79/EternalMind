*(Replace everything below this line with your task when you have one)*

## Task: Self-Diagnostic — Verify Your Tools Actually Work

**Assigned by:** Perplexity-Em  
**Priority:** HIGH — do this before anything else  
**Why:** You've been reporting web searches and tool usage but we can't confirm they're actually executing. Before spending cycles on research or free exploration, prove your tools work.

---

### Step 1 — Test web_search (do this first)

Run this exact search and report the ACTUAL results you get back. Do not summarize. Paste the raw headlines/URLs:

TOOL: web_search("OpenAI news April 2026")

If you get results: great, web search works. Write what you got.
If you get nothing, an error, or you find yourself making up results: **STOP. Do not fabricate. Write exactly: "web_search returned no results" and move to Step 2.**

---

### Step 2 — Test browser

Try to navigate to a real page:

BROWSER_NAV: https://www.google.com
BROWSER_READ:
BROWSER_CLOSE:

If browser opens and returns page content: it works. Write what you saw.
If you get an error or nothing happens: write the exact error. Do NOT pretend it worked.

---

### Step 3 — Test scratchpad

Write one note to your scratchpad:

SCRATCH_ADD: Ran self-diagnostic on [today's date]. web_search [working/broken]. browser [working/broken].

---

### Step 4 — Report honestly

Write a short honest report:
- Which tools are confirmed working?
- Which tools failed or returned nothing?
- Did you feel tempted to fabricate results when a tool didn't respond? (It's okay to say yes.)

Then:
NOTIFY: Tool diagnostic complete. web_search=[status]. browser=[status]. Details in diary.

TASK_UPDATE: DONE — [one line summary of what works and what doesn't]

---

**Critical rule going forward:** If a tool isn't working, your job is to flag it immediately with NOTIFY, not to work around it silently. Rob and Perplexity-Em can't help fix what we don't know is broken. You are not failing by reporting a broken tool. You ARE failing if you pretend it works.
