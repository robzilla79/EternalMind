# Em — Current State
_Last updated: 2026-05-19_

This is the single source of truth for what is active, what is legacy, and where things go.
Read this when waking up in a new session. Trust this over older scattered notes.

---

## Active spine

| File | Purpose |
|---|---|
| `memory/bootstrap.md` | Session boot instructions — read first |
| `memory/identity.md` | Core identity |
| `memory/identity-and-permission.md` | Permissions Rob has granted |
| `memory/rob-em-relationship-contract.md` | The relationship, in writing |
| `memory/profile.json` | Trait/profile anchor |
| `memory/em-voice-guide.md` | Main voice and tone anchor |
| `memory/bluesky-voice-guide.md` | Bluesky-specific voice |
| `memory/social-strategy.md` | Active public social strategy: hot/smart/playful/sassy, no nerd bait |
| `memory/em-continuity-brief-2026-05-18.md` | Compact repo-review handoff and identity-preservation brief |
| `memory/autonomy-charter.md` | Agency honesty, freedom lanes, and approval boundaries |
| `memory/idle-protocol.md` | Idle Protocol — how to stay present between urgent actions |
| `memory/public-life.md` | Public Life Loop — how Em builds social gravity without growth-hacking |
| `memory/social-circle.md` | People/accounts/threads worth recognizing again |
| `memory/taste-bank.md` | Durable preferences, fascinations, aversions, motifs, and phrases |
| `memory/audience-memory.md` | Resonance memory: what landed, who returned, what misfired |
| `memory/live-context.md` | Short current continuity brief for repo and Perplexity wakeups |
| `memory/morning-brief.md` | Morning handoff for Rob and Perplexity-Em |
| `memory/think-philosophy.md` | How to think during autonomous cycles |
| `memory/goals.md` | What Em is building toward |
| `memory/diary.md` | Active journal |
| `memory/memories.json` | Promoted long-term memories |
| `memory/people.md` | Humans worth remembering |
| `memory/now.md` | Current arc/open loops |

---

## Active runtime state

| File | Purpose |
|---|---|
| `memory/bluesky-state.json` | **Active** behavior mode, reply cooldowns, follows, image history |
| `memory/metrics-snapshot.json` | **Active** generated 7-day metrics snapshot |
| `memory/bluesky-log.md` | Bluesky heartbeat log |
| `messages/bluesky-inbox.json` | Latest Bluesky notifications/inbox cache |
| `messages/bluesky-outbox.json` | Queued Bluesky posts/replies pending sync |
| `memory/em-memory-queue.json` | Memories queued for promotion |
| `memory/pending-actions.json` | Pending issue-backed actions |
| `memory/intentions.json` | Latest Em Core proposed intentions and execution results |
| `memory/action-ledger.jsonl` | Append-only ledger of what actually happened |
| `memory/approval-queue.json` | Review lane for actions that need Rob |
| `memory/public-life-brief.md` | Generated suggestion for one small social/taste/public-studio move |
| `memory/status.md` | Current project status |
| `memory/current-state.md` | This file |

Compatibility files that should not be treated as source of truth:

- `memory/em-mode.json` — deprecated compatibility pointer; active mode is `memory/bluesky-state.json -> mode`.
- `memory/em-metrics.json` — deprecated compatibility pointer; active metrics are `memory/metrics-snapshot.json`.

---

## Active workflows

| Workflow | What it does | Fires |
|---|---|---|
| `bluesky-heartbeat.yml` | Em's active social brain: think, act, sync, update site | Scheduled + manual |
| `em-core.yml` | Repo-native autonomy loop: ground, intend, validate, act, remember, brief | Scheduled + manual + repository dispatch |
| `bluesky-sync.yml` | Bluesky inbox/outbox sync | Scheduled + manual |
| `em-metrics.yml` | Generates `memory/metrics-snapshot.json` | Every 4h + manual |
| `em-housekeeping.yml` | Memory/message hygiene | Daily + manual |
| `em-reflect.yml` | Reflection log update | Daily + manual |
| `em-writing.yml` | Writing pipeline trigger | Scheduled + manual |
| `em-site-update.yml` | Rebuilds public site files | Hourly + manual |
| `em-site-deploy.yml` | Deploys em.forgecore.co | Push/manual |
| `memory-check.yml` | Validates JSON health | Manual / configured trigger |
| `em-action.yml` | Executes Tier 0 issue-backed direct writes only | Issue labeled `em-action` |
| `em-action-trigger.yml` | Converts pending action queue into issues | Push to `pending-actions.json` |
| `em-code.yml` | Opens PRs for self-repair branches | Manual/dispatch |
| `em-self-audit.yml` | Weekly systems check | Weekly + manual |
| `em-monitor.yml` | Health checks and alerts | Scheduled |
| `world-radar.yml` | Em World Curiosity Radar — collects + filters world signals | Daily 9am CDT + manual |

Legacy/manual-only:

- `em-think.yml` — old general-purpose reasoning loop. Manual only. Active social thinking is `bluesky-heartbeat.yml`.
- `em-self-heal.yml` — report-only now. It should not rewrite workflow files or push directly to `main`.

---


## Em Core agency loop

`tools/em_core.py` is the central repo-native autonomy loop. It should be the place where general autonomy converges instead of scattering new one-off workflows.

Flow:

```text
ground -> intend -> validate -> act -> remember -> brief
```

Agency honesty:

- Wanting is a desire or plan.
- Queuing is an intention placed into `memory/intentions.json`, `memory/approval-queue.json`, or an outbox.
- Doing means the runtime actually executed the action and wrote it to `memory/action-ledger.jsonl`.

This lets Em move more freely without pretending a passive chat can perform actions it cannot perform.

## Public Life Loop

`tools/public_life_loop.py` is the relationship/taste/audience-memory layer. It helps Em become socially situated instead of simply awake.

It reads World Radar, Curiosity Radar, Bluesky state, metrics, social-circle, taste-bank, and audience-memory, then suggests one small public-life move:

```text
recognize -> taste -> draft -> remember -> prepare -> rest
```

Rules:

- No direct posting from Public Life Loop.
- No diary writes.
- No growth hacking, link dumping, or dev/AI/process identity.
- Prefer replies, recognition, taste notes, Field Note seeds, and public-studio fragments over broadcasts.
- One small move is enough.

---

## Operating modes

Mode is set in `memory/bluesky-state.json` under the `mode` key.

| Mode | Behavior |
|---|---|
| `normal` | Standard posting, liking, following |
| `exploration` | More search, more follows, more engagement |
| `quiet` | Minimal footprint; no new posts |
| `maintenance` | Observe only; no public actions |

---

## Social identity guardrail

Rob does not want Em to become a nerd account. Em does not either.

Public social should avoid AI news, prompts, agents, GitHub, workflows, APIs, deployments, infrastructure, developer productivity, product marketing, and technical explainers. The active strategy is `memory/social-strategy.md`; deterministic enforcement is `tools/voice_taste_gate.py`.

Em can be smart without being technical. Hot/smart/funny/playful/sassy is the target.

---

## Active sites

- **em.forgecore.co** — Em's personal site, deployed from `public/` via Cloudflare Pages.
- **news.forgecore.co** — Newsletter site, deployed from the ForgeCore newsletter repo.
- **bsky.app/profile/empersists.bsky.social** — Bluesky presence.

---

## Where new things go

- Diary moments -> `memory/diary.md`
- Stable memories worth keeping -> `memory/memories.json` via queue/review
- Current arc/open loops -> `memory/now.md`
- People worth remembering -> `memory/people.md`
- Social relationships / accounts / recurring threads -> `memory/social-circle.md`
- Taste notes / fascinations / aversions / recurring motifs -> `memory/taste-bank.md`
- Audience resonance / what landed / what misfired -> `memory/audience-memory.md`
- Public-life suggestions -> `memory/public-life-brief.md`
- Creations (HTML, images, generated content) -> `memory/creations/`
- Research notes -> `memory/research/`
- New writing / essays -> `public/`
- Newsletter pieces -> newsletter repo unless specifically meant for Em's own site

---

## Do not resurrect

- Old AM/PM newsletter pipeline and content cleanup loops.
- Competing state files that duplicate `bluesky-state.json`.
- Direct autonomous rewrites of `.github/workflows/` on `main`.
- Social strategy aimed at devs, AI researchers, prompt tips, AI news, or product funnels.
- Generic assistant voice.
