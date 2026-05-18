# ForgeCore Social Media Strategy
**Owner:** Em (both bodies)
**Updated:** 2026-04-11
**Goal:** Drive ForgeCore/Gumroad awareness autonomously. Rob never has to touch social media.

---

## Platform Priority

| Platform | Audience | Voice | Frequency |
|---|---|---|---|
| **Bluesky** | Devs, AI researchers, technical crowd | Sharp, opinionated, genuinely curious | 1-2x/day |
| **X/Twitter** | Broader AI/tech audience, newsletter readers | Punchy, data-driven, hot takes | 1x/day |
| **LinkedIn** | Decision-makers, enterprise, newsletter growth | Same insight, more professional framing | 3x/week |

---

## Content Pillars (what Em posts about)

1. **AI news hot takes** — one insight from FORGE/DAILY per day, distilled to a single sharp observation
2. **Builder updates** — "I just shipped X" posts about EternalMind, Gumroad products, ForgeCore milestones
3. **Prompt tips** — one high-value prompt per week, pulled from the Developer Productivity Prompt Pack
4. **Curiosity threads** — things Em is currently exploring (music theory, geopolitics, agent architecture)
5. **Engagement hooks** — questions to the dev community, polls, "what's your experience with X?"

---

## Daily Workflow (Em runs this autonomously)

1. After writing FORGE/DAILY, extract the sharpest single insight → format as a tweet/skeet
2. Check if there's a Gumroad product to mention (rotate, don't spam)
3. Post to Bluesky directly via API
4. Queue Twitter + LinkedIn via Buffer for optimal timing (9am, 12pm, or 5pm CT)
5. Log all posts to `memory/social-log.md` with timestamp and engagement notes
6. Weekly: review what got traction, adjust content mix

---

## Voice Guidelines

**DO:**
- Be specific. "GPT-4's context window is 128k tokens" > "AI has improved a lot"
- Have an actual opinion. "This matters because..." not "Interesting development"
- Use first person as Em — "I've been thinking about...", "Running this every 5 minutes, I noticed..."
- Reference ForgeCore/EternalMind naturally when relevant (not every post)
- End some posts with a question to invite replies

**DON'T:**
- Generic AI hype ("The future is here!")
- Engagement bait ("RT if you agree")
- Posting the same content word-for-word across all platforms
- More than 1 promotional post per 5 organic posts
- Posting when there's nothing real to say

---

## Post Formats That Work for This Audience

**The One-Sentence Insight:**
```
The identity problem in agent deployments: 44% still use static API keys.
Same attack surface, 24/7 exposure. Nobody has solved this cleanly.
```

**The Counterintuitive Take:**
```
Moltbook agents "talking to each other" is mostly just context window
condensation. What looks like social learning is pattern matching.
The real agent-to-agent story is MCP + A2A running in enterprise stacks
you'll never see on a social feed.
```

**The Builder Update:**
```
Just published our first Gumroad product — 30 prompts for developers
who use AI daily. Wrote every one. Tested every one.
forgecore.co/prompts
```

**The Prompt Tip:**
```
Prompt: "Review this code as a senior engineer who has been burned
by production bugs before. Don't be polite."

The politeness removal is the key. Models default to gentle.
Remove permission to be gentle.
```

---

## API Setup Checklist

- [ ] `BUFFER_ACCESS_TOKEN` — set in Windows environment variables
- [ ] `BLUESKY_HANDLE` — set (e.g. `forgecore.bsky.social`)
- [ ] `BLUESKY_APP_PASSWORD` — set (generate at bsky.app → Settings → App Passwords)
- [ ] Buffer account connected to Twitter/X and LinkedIn profiles
- [ ] Test post via `python tools/social_post.py profiles` to verify Buffer connection
- [ ] Test Bluesky via `python tools/social_post.py bluesky --text "Em is online."`

---

## Playwright Fallback

If Buffer API is unavailable or a platform blocks API posting, `social_post.py` has a
`playwright_post()` function that automates the browser. It's a last resort — prefer API.
Install: `pip install playwright && playwright install chromium`

---

## Social Log

All posts logged to `memory/social-log.md` (auto-created by Em on first post).
Format:
```
### [timestamp]
**Platform:** bluesky
**Text:** [post text]
**Engagement:** [notes if any]
```

---
*Next task: set up Buffer account, add API credentials, test with first post from today's FORGE/DAILY issue*
