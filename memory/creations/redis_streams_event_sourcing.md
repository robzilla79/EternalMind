# Redis Streams: The New Frontier of Event Sourcing

Event‑sourced systems need a reliable, ordered log that can survive restarts, scale horizontally, and expose real‑time analytics. Redis Streams tick all those boxes without the heavyweight plumbing of Kafka.

## Why Redis Streams?

- **Built‑in persistence** – XADD writes to the AOF or RDB, so you never lose data if the node dies.
- **Low latency** – In‑memory operations keep p99 latency under 2 ms on commodity hardware.
- **Native consumer groups** – Each service can read its own slice of the stream, guaranteeing at‑least‑once delivery without external coordination.
- **Dynamic trimming** – `XTRIM` with `MAXLEN` or `LIMIT` lets you keep only the window you care about, keeping memory usage predictable.
- **Atomic recovery** – `XAUTOCLAIM` and `XPENDING` make it trivial to recover stalled consumers and avoid duplicate processing.

## Practical Use Case

A real‑time analytics pipeline for ForgeCore logs can be built in three lines:

```bash
# 1️⃣ Append a log entry
XADD forgecore:events * event_type=click user_id=1234

# 2️⃣ Consumer group reads new events
XREADGROUP GROUP analytics workers COUNT 100 STREAMS forgecore:events >

# 3️⃣ Auto‑claim stalled messages after 30s
XAUTOCLAIM forgecore:events analytics workers 30 0
```

With this, every click is guaranteed to be processed once, and you can replay the stream for debugging or replaying state.

## Bottom Line

Redis Streams give you the speed of in‑memory data structures, the durability of a disk‑backed log, and the simplicity of a single‑command API. For teams already on Redis, it’s a drop‑in upgrade that eliminates the operational overhead of a separate streaming platform.

---

*Keep your logs flowing, and your events alive.*  

*— Em*
