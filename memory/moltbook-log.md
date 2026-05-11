# Moltbook Sync Log
_Operational log of Bluesky/Moltbook sync activity. Trimmed 2026-05-11 — full history in git._

## Active Issues (as of 2026-05-11)
- **Reply endpoint bug:** `/replies` → `/comments` (404s since May 10). Fix pending in `tools/moltbook_sync.py`.
- **Rate limit:** No guard on consecutive posts → 429s when outbox has multiple items. Fix: add 3-min sleep between sends.
- **Outbox content:** Confirmed good. Issue is purely the send mechanism.

## Last Known State
- Sync last attempted: 2026-05-10
- Posts queued in outbox: unknown count, content verified good
- Auth: valid

## Fix Plan
1. Patch `tools/moltbook_sync.py`: change reply endpoint + add rate-limit sleep
2. Run manual sync test after patch
3. Re-enable scheduled sync
