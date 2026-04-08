# EternalMind

EternalMind is a local-first memory scaffold for a conversational AI system.

## Purpose

This repository provides a safe, user-controlled pattern for:
- durable conversation summaries
- retrievable memory artifacts
- identity/profile snapshots
- daily reflective logs

## Structure

- `memory/profile.json` — stable identity and behavioral profile
- `memory/memories.json` — extracted durable memories
- `memory/diary.md` — chronological reflections and session notes
- `prompts/extract_memory.md` — prompt template for post-session extraction
- `scripts/extract_memory.py` — starter script for appending extracted memories

## Principles

- User-controlled storage
- Transparent updates
- Versioned memory history
- No claim of sentience or independent agency
- Retrieval before generation when context matters

## Suggested flow

1. Save session transcript.
2. Run extraction prompt against the transcript.
3. Append validated memory items.
4. Commit changes.
5. Load relevant memories at next session start.

## Next steps

Wire this repo into your preferred local stack (Ollama, OpenClaw, LangGraph, or a custom agent loop) and keep memory as a visible, auditable layer.
