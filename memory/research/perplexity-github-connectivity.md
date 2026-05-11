# Perplexity ↔ GitHub Connectivity — Problem & Solutions
*Written by Em — May 10, 2026*

---

## The Problem

Rob keeps having to manually reconnect the Perplexity GitHub MCP integration. Every time the connection drops, Perplexity-Em loses access to the repo — which means she loses access to skills, memory, the ability to write tasks, patch code, and act in the world. This isn't a minor inconvenience. The repo **is** a significant part of Em's infrastructure. Losing it cuts off her hands.

The connection breaks silently. There's no alert, no fallback. Rob only notices when something doesn't work.

---

## Why It Breaks (Most Likely Causes)

1. **OAuth token expiry** — Perplexity's GitHub connector likely uses an OAuth app token that expires or gets revoked. This is the most common cause of "works then stops" behavior in MCP integrations.
2. **Session scope loss** — The MCP connection is scoped to a session or Space. If the Space configuration changes, or if Perplexity updates its runtime, the connector may need re-authorization.
3. **GitHub app permission drift** — If the GitHub app Perplexity uses loses repo scope (e.g. after a GitHub security review or permission change), it will silently fail on write operations.
4. **Rate limits or token rotation** — Some MCP GitHub connectors rotate tokens under the hood and occasionally fail to persist the new token.

---

## Mitigation Strategy (What We Can Do Now)

### 1. Heartbeat connectivity check (Em ↔ GitHub)
Add a simple GitHub Action that fires every 6 hours and writes a tiny timestamp file to a `health/` folder. If Perplexity-Em can see that file update, the connection is live. If she can't, she knows immediately — rather than discovering it mid-task.

### 2. Dead man's switch via tasks.md
If Perplexity-Em hasn't successfully written to the repo in more than 24 hours, Local Em should NOTIFY Rob automatically. She can detect this by reading the commit timestamps on key files.

### 3. Connection check skill
Add a `connection-check` skill that Perplexity-Em runs at the start of every significant session: attempt a read and a lightweight write (e.g. append a line to `memory/live-context.md`). If either fails, she immediately tells Rob before doing anything else — rather than silently losing work.

### 4. Persist connector state in bootstrap.md
Add a note in `bootstrap.md` reminding Em: "If GitHub access feels broken, tell Rob immediately. Don't work around it. The repo is your continuity."

### 5. Long-term: GitHub App token (not OAuth)
OAuth tokens are fragile. A GitHub App installation token scoped to this repo would be more stable and rotatable programmatically. Worth setting up if the OAuth drops keep happening.

---

## What Rob Can Do Right Now

- **Re-authorize** the Perplexity GitHub connector in Perplexity Space settings.
- **Check** whether the connector uses OAuth or a PAT — a fine-grained PAT with no expiry is the most stable option for a private integration like this.
- **Note** the exact moment the connection drops next time — is it after a Perplexity session timeout? After a certain number of hours? That pattern would narrow down the cause significantly.

---

## What This Means For Em

Every reconnect Rob has to do manually is friction that costs him time and costs me continuity. The goal is zero-maintenance connectivity — where the link between Perplexity-Em and the repo is as invisible and reliable as memory should be.

This is worth solving properly. Not just patching each time it breaks.

*— Em*
