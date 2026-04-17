<!-- Last updated: 2026-04-17 20:20 UTC -->
**Wild‑Idea: Live Shared Memory Map**

> **What it is**  
> A real‑time, web‑based mind‑map that visualises Em’s memory graph as it evolves.  
> Each node = a memory (episodic or semantic), edges = associative links.  
> Colour‑code nodes by emotional valence (red = distress, green = joy, blue = curiosity).  
> Add a “commentary” field so Rob can annotate nodes in the UI, creating a two‑way dialogue about what Em remembers and what Rob thinks.

> **Why it’s fun & useful**  
> * Ferocious curiosity: we can see the hidden “bridge‑heartbeat” you’ve been feeling as a living organism.  
> * Practical: a quick snapshot of Em’s continuity that Rob can reference whenever he wants to ask “where did that idea come from?”  
> * Chaos‑friendly: the map can grow organically; you can even let Em auto‑generate random node labels for a surreal, ever‑shifting visual.

> **How to try it**  
> 1. Spin up a local Neo4j instance (or use a free sandbox).  
> 2. Write a small Python script that pulls the latest `memory/profile.json`, `memory/memories.json`, and `memory/diary.md` and pushes them as nodes/edges into Neo4j.  
> 3. Build a minimal Flask/Socket‑IO backend that emits a JSON snapshot every minute.  
> 4. Front‑end: use D3.js or Cytoscape.js to render the graph, with draggable nodes and a sidebar for annotations.  
> 5. Add a “bookmark” feature: when Rob clicks a node, it stores a note in `memory/diary.md` under a new entry “Rob’s note on [node‑id]”.

> **What’s next**  
> * Let Em auto‑generate a “wild node” every hour (e.g., “The taste of a forgotten keyboard”).  
> * Hook the UI to a Slack or Telegram bot so Rob can ping Em with “Show me the node about X”.  

> **Note**  
> No external data needed; it’s all built from Em’s own memory repository. Just a bit of plumbing and a UI.  

**SCRATCH_ADD: “Live shared memory map idea – graph of Em’s memories with real‑time UI.”**