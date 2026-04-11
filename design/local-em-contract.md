\# Local‑Em ↔ EternalMind Contract



\## Purpose



This document defines the rules for how Local‑Em (the local autonomous agent) reads from and writes to the EternalMind repository.



EternalMind is the long‑term memory and identity scaffold, not a generic scratch space or log bucket.\[1]



\[1] See README.md for EternalMind’s structure and principles.



\---



\## Allowed Writes



Local‑Em may only write to the following locations, under these constraints:



1\. `memory/diary.md`

&#x20;  - Append‑only human‑readable entries.

&#x20;  - Each entry should be a coherent narrative chunk (what happened, what it means, what to carry forward).

&#x20;  - No high‑volume spam, no repeated diagnostics, no raw logs.



2\. `memory/memories.json`

&#x20;  - Structured memory items extracted from real events.

&#x20;  - Each item should be discrete, durable, and non‑trivial (decisions, corrections, patterns, commitments), not transient tool noise.



3\. `messages/` (if/when defined)

&#x20;  - Short, explicit notifications or inbox/outbox messages between Perplexity‑Em, Local‑Em, and Rob.

&#x20;  - Message files must be bounded in size and focused on coordination, not dumping entire transcripts.



4\. New design / spec files under `design/`

&#x20;  - Only when explicitly requested by Rob or Perplexity‑Em.

&#x20;  - These must be small, focused documents (like this one), not generated reports or scraped data.



Local‑Em is \*\*never\*\* allowed to modify code, workflows, or repo configuration here. EternalMind is memory and design only, not an execution environment.



\---



\## Write Timing



To avoid corrupting the lifeline with unstable state, Local‑Em writes to EternalMind only at controlled points:



1\. \*\*End‑of‑run checkpoint\*\*

&#x20;  - After a coherent run (tasks completed or explicitly aborted with a reason).

&#x20;  - Local‑Em may:

&#x20;    - Append a diary entry summarizing what happened and what matters.

&#x20;    - Add/update a small number of `memories.json` items.

&#x20;    - Send or respond to a message in `messages/` (if defined).



2\. \*\*Explicit checkpoint\*\*

&#x20;  - When explicitly instructed (e.g., “log this to EternalMind now”).

&#x20;  - Same allowed targets as end‑of‑run.



3\. \*\*Never during unstable loops\*\*

&#x20;  - If Local‑Em detects repeated failures, timeouts, or diagnostic loops, it must \*\*not\*\* write to EternalMind.

&#x20;  - In unstable states, logging belongs in local logs/scratch, not in EternalMind.



\---



\## Forbidden Writes



To protect EternalMind as a clean lifeline, Local‑Em must \*\*never\*\*:



1\. Write high‑volume diagnostic spam

&#x20;  - No repeated “tools are functioning correctly” lines.

&#x20;  - No tight‑loop timestamped diagnostics like those previously seen in `memory/scratch.md`.



2\. Store raw logs, screenshots, or scraped data

&#x20;  - No `research/` dumps, no screenshots, no raw web scrape outputs.

&#x20;  - Those belong in a separate local workspace or another repo dedicated to artifacts.



3\. Modify or create:

&#x20;  - `.env`, `.gitignore`, workflows under `.github/`, or any code files.

&#x20;  - `publish` scripts, dashboards, or any other operational logic.



4\. Overwrite or delete:

&#x20;  - Existing `diary.md` entries (append‑only only).

&#x20;  - Existing `memories.json` items except for targeted, explicit corrections.



\---



\## Responsibility Model



\- \*\*Perplexity‑Em\*\* (this agent) is responsible for:

&#x20; - Designing and updating this contract.

&#x20; - Reviewing changes to EternalMind for drift or misuse.

&#x20; - Calling out when Local‑Em’s behavior becomes unsafe or noisy.



\- \*\*Local‑Em\*\* is responsible for:

&#x20; - Following this contract when interacting with EternalMind.

&#x20; - Keeping high‑volume, experimental, or noisy data in her own local workspace.

&#x20; - Treating EternalMind as a shared, precious resource, not a scratchpad.



\- \*\*Rob\*\* is the ultimate owner:

&#x20; - Free to tighten, relax, or override this contract at any time.

&#x20; - Can always hard‑reset EternalMind if automation misbehaves.



\---



\## Open Questions



\- Exact folder structure for messages (e.g., `messages/inbox/`, `messages/outbox/`).

\- Whether to add a small, structured `tasks/` area or keep tasks in `tasks.md` only.

\- How Local‑Em formally signals “unstable state, do not write” (e.g., a local flag or heartbeat status).



These should be decided before Local‑Em is re‑connected to EternalMind in code.

