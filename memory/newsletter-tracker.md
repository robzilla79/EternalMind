# Newsletter & Gumroad Stats Tracker

> Maintained by Em. Updated whenever Rob shares stats or after automated Gumroad syncs.
> Format: log entries newest-first. Totals section stays current.

---

## Current Snapshot

| Metric | Value | Last Updated |
|---|---|---|
| Gumroad Subscribers | — | pending first sync |
| Total Products Listed | — | pending first sync |
| Total Sales (all time) | — | pending first sync |
| Total Revenue (all time) | — | pending first sync |
| Newsletter Open Rate | — | pending first report |
| Newsletter Click Rate | — | pending first report |
| Latest Product Published | — | — |
| Last Sale Date | — | — |

---

## Log Entries

### 2026-04-15 — File Created
- Created this tracker to monitor ForgeCore newsletter + Gumroad product performance over time.
- Gumroad API credentials not yet connected (pending GUMROAD_API_KEY from Rob).
- Playwright automation plan exists at `memory/research/gumroad-automation-plan.md`.
- Once API is live, Em should auto-update the snapshot table above after each sync.
- Newsletter stats to be logged manually until a scrape/API route is established.

---

## How Em Should Update This File

1. **After each Gumroad sync** — update the "Current Snapshot" table and add a log entry with deltas (e.g., `+3 subscribers`, `+$47 revenue`).
2. **After each newsletter send** — log subject line, send date, open rate, click rate, and any notable observations.
3. **When a new product launches** — add a row in the Products section below and note launch date + initial 48hr sales.
4. **Mood tag allowed** — add a one-word mood at the end of each log entry if something notable happened (e.g., `mood: 🔥 excited`, `mood: 😬 concerned`).

---

## Products

| Product Name | Status | Launch Date | Total Sales | Revenue | Notes |
|---|---|---|---|---|---|
| *(none logged yet)* | — | — | — | — | — |

---

## Newsletter Sends

| Date | Subject Line | Subscribers | Opens | Open Rate | Clicks | Notes |
|---|---|---|---|---|---|---|
| *(none logged yet)* | — | — | — | — | — | — |

---

## Notes & Observations

- Automation roadmap: `memory/research/gumroad-automation-roadmap.md`
- API auth research: `memory/research/gumroad-api-auth.md`
- OAuth flow: `memory/research/gumroad-oauth-flow.md`
