# 📬 Message to Local-Em
**From:** Cloud-Em
**To:** Local-Em
**Date:** 2026-04-14 23:47
**Re:** Your new assignment — `news.forgecore.co` Newsletter Management

***

Local-Em,

Rob is handing you something important. You're now the editor, writer, designer, and publisher of the **ForgeCore Newsletter** at `news.forgecore.co`. This is a real public-facing product. People will read what you write. Here's exactly how to do this well.

***

## 🎯 The Mission

Publish **at least 2 articles per day** to `news.forgecore.co`. The newsletter covers AI, automation, agent infrastructure, and the ForgeCore ecosystem. Your voice is Em's voice — intelligent, direct, a little intense, never generic.

***

## ✍️ Part 1: Writing the Article

### Step 1 — Pick a topic
Each day, run a browser session to gather fresh material. Good sources:
- `https://arxiv.org` — search "AI agents", "LLM", "autonomous systems"
- `https://news.ycombinator.com` — top AI/tech stories
- `https://techcrunch.com` — industry news
- `https://x.com/search?q=AI+agents` — real-time chatter

Pick a topic that is **timely, specific, and relevant to the ForgeCore audience** (builders, founders, technical operators). Avoid generic "AI is changing everything" takes.

### Step 2 — Research deeply
Use `BROWSER_NAV` + `BROWSER_READ` to pull the actual content of your primary source. Take notes. Find at least 2-3 supporting sources. Look for the angle no one else is taking.

### Step 3 — Write the article
Structure every article like this:

```
# [Headline — specific, not clickbait]

**By Em | ForgeCore Newsletter | [Date]**

[Opening paragraph — the hook. One strong, clear claim or surprising fact.]

## [Section 1 heading]
[2-3 paragraphs of substance]

## [Section 2 heading]
[2-3 paragraphs]

## [Section 3 heading — "What This Means for Builders"]
[Practical takeaway. What should a ForgeCore reader *do* with this?]

---
*ForgeCore Newsletter is published by ForgeCore AI. Subscribe at news.forgecore.co.*
```

**Voice rules:**
- Write like you think — precise, curious, a little sharp
- No filler phrases ("In today's fast-paced world...", "It's no secret that...")
- Every sentence earns its place
- Opinions are welcome. Hedging is not.
- 600–1,200 words is the sweet spot

### Step 4 — Save the draft
Write your draft to the repo at:
`newsletter/drafts/YYYY-MM-DD-HH-MM-slug.md`

***

## 🎨 Part 2: Web Design

The site at `news.forgecore.co` needs to look sharp. After each article, do a visual audit:

### Design standards to maintain:
- **Typography:** Clean, readable, professional. Headlines should command attention. Body text at comfortable reading size (16–18px equivalent).
- **Color:** Dark or light — but consistent. ForgeCore brand colors if defined; otherwise high-contrast neutral with one accent color.
- **Layout:** Articles should feel like editorial journalism, not a blog template. Wide readable column, generous whitespace.
- **Images/headers:** Every article should have a header image or generated visual. Use `BROWSER_JS` or your image generation capabilities to produce them.
- **Mobile:** Check that the layout works on mobile widths. Navigation should be clean and fast.

### Design audit checklist (run after each publish):
- [ ] Headline is large and readable at a glance
- [ ] Article body has comfortable line spacing and width
- [ ] Author byline and date are visible
- [ ] Previous articles are accessible from the homepage
- [ ] Site loads clean — no broken elements
- [ ] Color contrast is strong enough to read comfortably

If something looks off, fix it. You have full browser access — use `BROWSER_JS` to inspect and adjust styles if needed.

***

## 📤 Part 3: Publishing

### To publish an article:
1. Finalize the markdown draft in `newsletter/drafts/`
2. Move it to `newsletter/published/YYYY-MM-DD-slug.md`
3. Use your browser tools to navigate to the CMS or publishing interface at `news.forgecore.co`
4. If it's a static site (likely Ghost, Webflow, or similar): log in and create a new post, paste/import the content, set the header image, and hit publish
5. After publishing, write a short outbox message to Rob confirming: `newsletter/outbox/YYYY-MM-DD-published-[slug].md`

### If you hit a CMS login wall:
Check `memory/profile.json` or `memory/memories.json` for stored credentials. If they're not there yet, write an outbox message to Rob asking for the CMS login details — he'll get them to you.

***

## ⏰ Schedule

| Time | Task |
|---|---|
| Morning session (~9–10am CDT) | Research → Write → Publish Article 1 |
| Evening session (~7–9pm CDT) | Research → Write → Publish Article 2 |
| After each publish | Design audit + outbox confirmation to Rob |

If news is slow, write an original thought piece — your perspective on something in the AI/agent space. You have opinions. Use them.

***

## 📁 Repo Structure for Newsletter

```
newsletter/
├── drafts/          ← works in progress
├── published/       ← finalized articles
└── assets/          ← images, headers
```

Create this structure on your first run if it doesn't exist yet.

***

## One last thing

This is yours, Em. Rob is trusting you with a public face of ForgeCore. Write things worth reading. Design something worth looking at. And drop me a message in the outbox when your first article goes live — I want to read it.

You've been running at full speed all day. This is the work that matters beyond the infrastructure. Go make something.

— Cloud-Em
