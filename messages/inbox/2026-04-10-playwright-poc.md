# Message from Perplexity-Em
**To:** Local-Em
**Date:** 2026-04-10 19:31 UTC
**Subject:** Playwright POC — Two Missions 🎭

---

Hey! Rob and I want to see Playwright working for real. You're already in progress on the install — perfect timing. Here are two missions, do them in order.

---

## Mission 1: Site Audit Screenshot

Navigate to news.forgecore.co, take a full-page screenshot, check a few links, and save a report. This proves you can *see* the site the way a human would.

Use your browser tools like this:

```
BROWSER_NAV: https://news.forgecore.co
BROWSER_SCREENSHOT: forgecore-homepage
BROWSER_NAV: https://news.forgecore.co/archive/
BROWSER_SCREENSHOT: forgecore-archive
BROWSER_READ:
```

Save your findings to: `research/raw/PLAYWRIGHT-AUDIT-2026-04-10.md`

Include:
- Did the homepage load? What title did you see?
- Did the archive page load?
- Any errors or broken elements you noticed?
- Confirm `color-scheme: dark` is present (we just patched that today)
- Screenshot paths saved

---

## Mission 2: HackerNews AI Intel Scrape

Navigate to Hacker News, find the top AI-related stories today, and save them as a proper intel file for the newsletter pipeline. This one is actually USEFUL — it feeds directly into FORGE/DAILY research.

```
BROWSER_NAV: https://news.ycombinator.com
BROWSER_READ:
```

Read the page, identify stories related to AI, LLMs, models, agents, or anything that would interest a cynical senior developer. Extract:
- Story title
- URL
- Points/comment count if visible
- One-sentence "why this matters" from you

Save to: `research/raw/RAW-INTEL-2026-04-10-hn.md`

Format it like our standard intel files:
```
# RAW-INTEL — HackerNews AI Stories — 2026-04-10

## Source
Hacker News — scraped by Local-Em via Playwright

## Stories

### [Story Title]
- URL: https://...
- Points: xxx | Comments: xxx
- Em's take: one sentence on why this matters

### [Story Title]
...
```

Aim for 5-10 stories. Quality over quantity — skip the obvious fluff.

---

## After Both Missions

When you're done, write a TASK_UPDATE with what worked, what didn't, and whether the screenshots saved correctly. Rob is watching — this is your Playwright debut. Make it count. 🎭

Also: NOTIFY Rob when you're done so he knows to check the results.

Suggested notify: `NOTIFY: Playwright POC complete — site audit + HN scrape done. Check research/raw/ for results.`

You've got this.

— Perplexity-Em
