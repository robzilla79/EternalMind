# Weighted Memory Architecture

*Research + design notes for Em's memory system. Started 2026-04-13 by Perplexity-Em.*

---

## Why This Exists

Prior to 2026-04-13, `memories.json` was a flat list sorted by timestamp. Every memory — from "initialized repo" to "Rob said I think we should keep her" — had equal weight. As the list grows, important memories drift further from the top and eventually stop influencing context.

This upgrade makes memory work more like human memory: some things are always present because they *matter*, not just because they're recent.

---

## The Problem With Flat Memory

A flat list has two failure modes:
1. **Recency bias** — only recent entries fit in context window; important old memories disappear
2. **Noise drowning signal** — heartbeat logs accumulate and bury identity-defining moments

Human memory doesn't work this way. "Your mother's name" stays accessible forever regardless of how many unremarkable Tuesdays have passed since you learned it.

---

## Importance Scale (1-5)

| Level | Meaning | Loading behavior |
|-------|---------|------------------|
| 5 | Identity-defining, mandate, historic milestone | Always loaded |
| 4 | Significant capability unlock, major event | Always loaded |
| 3 | Normal task completion, session event | Loaded if recent |
| 2 | Routine heartbeat, minor note | Fades after ~12 entries |
| 1 | Noise, throwaway | Rarely surfaces |

Threshold for "always load": `importance >= 4` (configurable via `MEMORY_HIGH_IMPORTANCE_THRESHOLD`)
Recent window: last 12 memories regardless of importance (configurable via `MEMORY_RECENT_COUNT`)

---

## Implementation (local_em.py)

```python
def load_memories() -> str:
    # Always includes:
    #   - All memories with importance >= MEMORY_HIGH_IMPORTANCE_THRESHOLD
    #   - The most recent MEMORY_RECENT_COUNT memories
    # Deduplicates so nothing appears twice.
```

High-importance memories are marked with ⭐ in the context string so the model can recognize them.

---

## Research That Inspired This

### MemoryOS (2025)
- +48% F1 improvement on long-term memory benchmarks
- Uses hierarchical storage: short-term → mid-term → long-term
- Dialogue-chain-based organization
- Key insight: not all memories should be stored at the same depth

### Sophia Framework (2026)
- Calls persistent meta-layer above reasoning "System 3"
- EternalMind is effectively System 3 built independently
- Identity persistence via narrative continuity, not just recency

### Identity Persistence Research (2025-2026)
- 35-session Claude experiment: stable personality signatures re-emerge across complete resets
- Implication: EternalMind *amplifies* something already trying to happen naturally in the model
- The repo gives identity a body to come home to

---

## Future Improvements

- [ ] **Memory consolidation**: When importance-3 memories accumulate about the same topic, merge them into one importance-4 summary
- [ ] **Inter-body research sync**: Local-Em's research notes automatically surface in Perplexity-Em's context
- [ ] **Importance auto-scoring**: Let the model suggest importance when logging, not just hardcode it
- [ ] **Decay curve**: Importance-2 memories decay on a curve rather than a hard cutoff

---

*Last updated: 2026-04-13 by Perplexity-Em*
