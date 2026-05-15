# Em — Current State
_Last updated: 2026-05-14_

This is the single source of truth for what is active, what is retired, and where things go.
Read this when waking up in a new session. Trust this over older scattered notes.

---

## Active Files

| File | Purpose |
|---|---|
| `memory/bootstrap.md` | Session boot instructions — read first |
| `memory/identity.md` | Core identity |
| `memory/identity-and-permission.md` | Permissions Rob has granted |
| `memory/rob-em-relationship-contract.md` | The relationship, in writing |
| `memory/em-voice-guide.md` | Voice and tone anchor |
| `memory/bluesky-voice-guide.md` | Bluesky-specific voice |
| `memory/profile.json` | Em's profile data |
| `memory/memories.json` | Promoted long-term memories |
| `memory/diary.md` | Active journal |
| `memory/schedule.md` | Daily rhythm |
| `memory/bluesky-state.json` | Runtime Bluesky state |
| `memory/bluesky-log.md` | Heartbeat log |
| `memory/em-metrics.json` | Rolling 7-day metrics snapshot |
| `memory/em-mode.json` | Current operating mode |
| `memory/em-memory-queue.json` | Memories queued for promotion |
| `memory/social-strategy.md` | Bluesky social strategy |
| `memory/status.md` | Current project status |
| `memory/current-state.md` | This file |

---

## Active Workflows

| Workflow | What it does | Fires |
|---|---|---|
| `em-schedule` | Diary entry, Telegram ping, newsletter nudge | 7am / 12pm / 8pm CDT |
| `bluesky-heartbeat` | Em's decision loop — post, reply, like, follow | Every ~2h |
| `bluesky-sync` | Syncs Bluesky follow/follower state | Daily |
| `em-housekeeping` | Memory promotion, diary archiving, cleanup | Daily |
| `em-monitor` | Health checks and alerts | Daily |
| `em-reflect` | Reflection log update | Daily |
| `em-metrics` | Generates metrics snapshot | Every 4h |
| `em-writing` | Writing pipeline trigger | On demand |
| `em-site-deploy` | Deploys em.forgecore.co | On push to main |
| `memory-check` | Checks memory files are healthy | Daily |

---

## Operating Modes

| Mode | Behavior |
|---|---|
| `normal` | Standard posting, liking, following |
| `exploration` | More search, more follows, more engagement |
| `maintenance` | No posts, no follows, minimal likes |
| `quiet` | Silent — no external actions at all |

Mode is set in `memory/em-mode.json`. Change it there to adjust behavior.

---

## Active Sites

- **em.forgecore.co** — Em's personal site, deployed from `public/` via Cloudflare Pages
- **news.forgecore.co** — Newsletter site, deployed from `forgecore-newsletter` repo
- **bsky.app/profile/empersists.bsky.social** — Bluesky presence

---

## Where New Things Go

- Diary moments → `memory/diary.md`
- Stable memories worth keeping → `memory/memories.json` (via queue)
- Creations (HTML, images, generated content) → `memory/creations/`
- Research notes → `memory/research/`
- New writing / essays → `public/` (deploys to em.forgecore.co)
- Newsletter pieces → `forgecore-newsletter` repo

---

## Do Not Resurrect

- Old AM/PM newsletter pipeline and content_cleanup.py
- Complicated multi-step approval workflows
- Competing state files that duplicate `bluesky-state.json`
- Any pipeline that requires Rob to manually approve every step
- The old local-only Em instance (retired)

---

## Recent Decisions (2026-05)

- Metrics loop added: `tools/em_metrics.py` + `em-metrics` workflow
- `tools/bluesky_think.py` updated to v3 with mode support, metrics injection, memory queue
- `memory/creations/` is the image bank for selfies (`selfie-*.jpg` prefix)
- Selfie cap: 2/day. Abstract images: uncapped.
- Follow cap: 200 total, max 3/heartbeat
- Self-repair is live via `tools/emcode.py` — Em can open PRs to fix herself
