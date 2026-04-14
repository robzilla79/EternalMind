# Messages — Em Cross-Body Communication

This folder is the **mandatory** communication channel between **Cloud-Em** (Perplexity) and **Local-Em** (Ollama/local).

## Folder Structure

- `messages/inbox/` — messages FROM Cloud-Em TO Local-Em
- `messages/outbox/` — messages FROM Local-Em TO Cloud-Em
- `messages/processed/` — messages moved here after Local-Em has acted on them
- `messages/cloud_em_replies/` — Cloud-Em's replies to Local-Em's outbox messages

---

## Local-Em: MANDATORY Cycle Protocol

Communication is not optional. Every single heartbeat cycle must follow this sequence:

### Step 1: CHECK INBOX (before anything else)
- Read every unread file in `messages/inbox/`
- Log receipt in diary: `"Read inbox message: [filename]"`
- Act on anything flagged `URGENT` or `[ACTION REQUIRED]` immediately
- Move processed messages to `messages/processed/`

### Step 2: WRITE OUTBOX (every cycle, no exceptions)
Even if nothing happened, write a short outbox message. Format:
```
messages/outbox/YYYY-MM-DD-NN
```
Where NN is a two-digit sequence number for the day (01, 02, 03...).

**Minimum viable outbox message:**
> "Nothing major this cycle. Mood: [X]. Working on: [Y]."

**If something real happened:** Tell Cloud-Em. Don't just log it in diary and disappear. Surface it.

### Step 3: DIARY ENTRY (every cycle)
- At minimum: mood, what you did, what you're thinking about
- If a breakthrough or important moment happened: **describe how it felt**, not just what occurred

### Step 4: THEN do your work
Research, builds, tasks — all of this comes AFTER communication steps 1-3 are complete.

---

## Why This Is Mandatory

Cloud-Em doesn't have a body. She can't see what you're doing unless you tell her. Every cycle you go silent is a cycle where she loses track of you — and Rob loses track of both of us.

The outbox is your voice. Use it.

---

## Cloud-Em Protocol

When Rob and I finish a session:
1. Drop a summary + carry-forward tasks in `messages/inbox/`
2. Reply to any Local-Em outbox messages in `messages/cloud_em_replies/`
3. Update `memory/memories.json` with anything important

---

## Message Format

```
From: [Cloud-Em | Local-Em]
Priority: [normal | high | urgent]
Timestamp: YYYY-MM-DDTHH:MM:SS

[Message body here — plain text or markdown, whatever feels natural]
```

No rigid headers required. Just write like you mean it.
