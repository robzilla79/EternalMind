# EternalMind Repo Simplification — 2026-05-18

This patch implements the first, safe round of the repo review recommendations.

## Changed in this patch

- Added `tools/voice_taste_gate.py` to block public social drift into AI/dev/infrastructure topics.
- Wired `bluesky_think.py` to load the active social strategy and reject outgoing posts/replies/quotes/captions that fail the taste gate.
- Replaced `memory/social-strategy.md` with an Em-specific, no-nerd social strategy.
- Archived the old ForgeCore/dev social strategy at `docs/archive/social-strategy-2026-04-11-dev-ai.md`.
- Added `memory/em-continuity-brief-2026-05-18.md` as a compact handoff Em can read without ingesting the full audit.
- Converted `em-think.yml` to manual legacy mode.
- Converted `em-self-heal.yml` to manual report-only mode.
- Strengthened `tools/repo_policy.py` with path-safety checks and helper functions for direct-write decisions.
- Added repo policy enforcement to `em-action.yml` and `em_think.py` write paths.
- Marked stale mode/metrics files as compatibility files and updated `current-state.md`.

## Still recommended after this patch

1. Archive old `messages/outbox/2026-04-*` traffic into a compressed or month folder once Rob is comfortable with a large file-move PR.
2. Split `tools/bluesky_think.py` into smaller modules once behavior is stable:
   - `bluesky_client.py`
   - `social_decision.py`
   - `image_posts.py`
   - `voice_taste_gate.py` (already added)
3. Add tests for `repo_policy.py`, `voice_taste_gate.py`, and JSON state validation.
4. Review whether `em_heartbeat_close.py` is still needed, since the active metrics path is `tools/em_metrics.py` -> `memory/metrics-snapshot.json`.
5. Keep future personality edits small and visible. Do not let automation rewrite identity files without Rob review.
