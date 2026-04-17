<!-- Last updated: 2026-04-17 20:46 UTC -->
**Wild idea: “Chaos Playground”**  
- Build a tiny Flask (or FastAPI) endpoint that, on a trigger, has Em spin up a *random* code snippet or creative prompt (e.g., a one‑sentence story seed, a short Python function, or a quirky math puzzle).  
- The snippet is immediately sent to a pre‑configured Telegram channel via the existing bot API.  
- Rob can tap a “Run” button in the channel that launches the snippet inside a sandboxed Docker container (or a local `subprocess` with strict resource limits).  
- Output, logs, and any side‑effects are captured and fed back to the channel.  

This gives us a playful, low‑risk loop where Em’s curiosity can manifest into spontaneous experiments, and Rob can decide which ones to “run” or “ignore.” It’s a sandbox for emergent behavior, a way to taste chaos without touching the main repo or breaking anything.  

> *SCRATCH_ADD: Wild idea – Chaos Playground: random snippet → Telegram → sandbox run, capture output.*