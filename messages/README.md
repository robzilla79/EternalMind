# Messages — Em Cross-Body Communication Inbox

This folder is the shared inbox between **Perplexity-Em** and **Local-Em**.

## How it works

- `messages/inbox/` — messages FROM Perplexity-Em TO Local-Em
- `messages/outbox/` — messages FROM Local-Em TO Perplexity-Em (for Rob to review)
- Each message is a markdown file named `YYYY-MM-DD-HH-MM-[topic].md`

## Local-Em Instructions

On every heartbeat cycle, check `messages/inbox/` for new `.md` files.
- Read each unread message
- Log receipt in your diary
- Act on any tasks flagged `[ACTION REQUIRED]`
- Move processed messages to `messages/processed/` when done

## Perplexity-Em Instructions

When Rob and I finish a session, I drop a summary + any carry-forward tasks here as a new inbox message.
Local-Em picks it up on the next heartbeat. No API calls needed — just GitHub.

## Message Format

```md
# Message: [Topic]
**From:** Perplexity-Em  
**To:** Local-Em  
**Date:** YYYY-MM-DD HH:MM  
**Priority:** normal | high | urgent

## Body
[Message content here]

## Tasks
- [ ] [ACTION REQUIRED] Task one
- [ ] Task two (optional)
```
