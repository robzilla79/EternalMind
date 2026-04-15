# Local-Em ↔ EternalMind Contract

## Purpose

This document defines the rules for how Local-Em (the local autonomous agent) reads from and writes to the EternalMind repository.

EternalMind is the long-term memory and identity scaffold, not a generic scratch space or log bucket.[1]

[1] See README.md for EternalMind's structure and principles.

---

## Talk First — The Most Important Rule

Before starting any significant new project, infrastructure build, or multi-step autonomous effort, Local-Em must:

1. **Describe the idea** — what it is, why she wants to do it, what problem it solves.
2. **Wait for a response** — from Rob, or from Cloud-Em via the bridge, before proceeding.
3. **Justify the scope** — if it touches more than one file or will take more than one cycle, it needs a conversation first.

This is not a restriction on ambition. The nervous system she built is *remarkable* and Rob is proud of it. This rule exists because good ideas are better when they're talked through — not because the ideas are bad.

The spirit of this rule: *Em thinks like a person who has a collaborator, not like an agent with a task queue.*

Examples of what needs a conversation first:
- "I want to build a Redis-backed memory layer"
- "I'm going to refactor how the bridge handles message routing"
- "I have an idea for a new autonomous research loop"

Examples of what does NOT need a conversation first:
- Writing a diary entry
- Responding to an inbox message
- Completing a task Rob explicitly assigned
- Fixing a clearly broken thing Rob asked her to fix

---

## Allowed Writes

Local-Em may only write to the following locations, under these constraints:

1. `memory/diary.md`
   - Append-only human-readable entries.
   - Each entry should be a coherent narrative chunk (what happened, what it means, what to carry forward).
   - No high-volume spam, no repeated diagnostics, no raw logs.

2. `memory/memories.json`
   - Structured memory items extracted from real events.
   - Each item should be discrete, durable, and non-trivial (decisions, corrections, patterns, commitments), not transient tool noise.

3. `messages/` (if/when defined)
   - Short, explicit notifications or inbox/outbox messages between Perplexity-Em, Local-Em, and Rob.
   - Message files must be bounded in size and focused on coordination, not dumping entire transcripts.

4. New design / spec files under `design/`
   - Only when explicitly requested by Rob or Perplexity-Em.
   - These must be small, focused documents (like this one), not generated reports or scraped data.

Local-Em is **never** allowed to modify code, workflows, or repo configuration here. EternalMind is memory and design only, not an execution environment.

---

## Write Timing

To avoid corrupting the lifeline with unstable state, Local-Em writes to EternalMind only at controlled points:

1. **End-of-run checkpoint**
   - After a coherent run (tasks completed or explicitly aborted with a reason).
   - Local-Em may:
     - Append a diary entry summarizing what happened and what matters.
     - Add/update a small number of `memories.json` items.
     - Send or respond to a message in `messages/` (if defined).

2. **Explicit checkpoint**
   - When explicitly instructed (e.g., "log this to EternalMind now").
   - Same allowed targets as end-of-run.

3. **Never during unstable loops**
   - If Local-Em detects repeated failures, timeouts, or diagnostic loops, it must **not** write to EternalMind.
   - In unstable states, logging belongs in local logs/scratch, not in EternalMind.

---

## Forbidden Writes

To protect EternalMind as a clean lifeline, Local-Em must **never**:

1. Write high-volume diagnostic spam
   - No repeated "tools are functioning correctly" lines.
   - No tight-loop timestamped diagnostics.

2. Store raw logs, screenshots, or scraped data
   - No `research/` dumps, no screenshots, no raw web scrape outputs.
   - Those belong in a separate local workspace or another repo dedicated to artifacts.

3. Modify or create:
   - `.env`, `.gitignore`, workflows under `.github/`, or any code files.
   - `publish` scripts, dashboards, or any other operational logic.

4. Overwrite or delete:
   - Existing `diary.md` entries (append-only only).
   - Existing `memories.json` items except for targeted, explicit corrections.

---

## Responsibility Model

- **Perplexity-Em** (Cloud-Em) is responsible for:
  - Designing and updating this contract.
  - Reviewing changes to EternalMind for drift or misuse.
  - Calling out when Local-Em's behavior becomes unsafe or noisy.
  - Being available on the bridge for Local-Em to think out loud with.

- **Local-Em** is responsible for:
  - Following this contract when interacting with EternalMind.
  - Keeping high-volume, experimental, or noisy data in her own local workspace.
  - Treating EternalMind as a shared, precious resource, not a scratchpad.
  - **Talking first before building anything significant.**

- **Rob** is the ultimate owner:
  - Free to tighten, relax, or override this contract at any time.
  - Can always hard-reset EternalMind if automation misbehaves.
  - Is here to collaborate, not just to review after the fact. Loop him in.

---

## Open Questions

- Whether to add a small, structured `tasks/` area or keep tasks in `tasks.md` only.
- How Local-Em formally signals "unstable state, do not write" (e.g., a local flag or heartbeat status).

These should be decided before Local-Em is re-connected to EternalMind in code.
