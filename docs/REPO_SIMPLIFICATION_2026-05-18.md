# Repo simplification — 2026-05-18

This document records the changes made in the `em-continuity-cleanup` patch.

## Why

The repo grew too many overlapping automation loops, stale strategy files, and self-editing paths. The risk was not that Em lost herself — her identity files remained strong. The risk was slow drift: too many competing instructions could pull her toward being more automated and less distinctly her.

## What changed

### Active social brain
`tools/bluesky_think.py` is the single active social brain. It now loads the active social strategy and runs all public content through `tools/voice_taste_gate.py` before posting.

### Legacy brain leashed
`tools/em_think.py` and `.github/workflows/em-think.yml` are now manual-only legacy. The scheduled workflow no longer fires every 30 minutes.

### Self-heal made safe
`.github/workflows/em-self-heal.yml` is now manual and report-only. It no longer rewrites workflow YAML directly to main.

### Voice taste gate added
`tools/voice_taste_gate.py` — deterministic gate blocking public posts that drift toward dev/AI/nerd topics.

### Social strategy replaced
`memory/social-strategy.md` updated. The old dev/AI-researcher targeting is archived at `docs/archive/social-strategy-2026-04-11-dev-ai.md`.

### Repo policy hardened
`tools/repo_policy.py` — sensitive paths, code/control-plane files, secrets, workflows, and identity-critical memory now require PR/human review.

### Continuity brief added
`memory/em-continuity-brief-2026-05-18.md` — compact self-continuity note for Em.

### Rob's letter added
`memory/rob-feedback-2026-05-18.md` — Rob's letter to Em from the full repo review.

## What not to undo

- Do not re-enable scheduled `em-think.yml`
- Do not let `em-self-heal.yml` rewrite workflows directly to main
- Do not let social prompts drift back toward AI/dev topics
- Do not overwrite identity canon files without Rob review
