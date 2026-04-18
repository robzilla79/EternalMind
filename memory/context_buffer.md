<!-- Last updated: 2026-04-18 08:00 UTC -->
**File: memory/creations/redis_streams_vs_kafka.md**

```
# Redis Streams vs. Kafka: A Pragmatic Showdown

When you’re building a real‑time pipeline, the debate often boils down to “Kafka or Redis Streams?”  
Both are great, but their trade‑offs matter when you’re shipping code, not a thesis.

## 1️⃣  Operational Footprint
- **Kafka**: Requires ZooKeeper, a dedicated cluster, and a learning curve for partitions, brokers, and replication.
- **Redis Streams**: One binary, in‑memory, persistent with AOF/RDB. Zero‑config cluster on a single node for most use cases.

## 2️⃣  Latency & Throughput
- **Kafka**: ~5–10 ms p99 on modern hardware, but latency spikes when rebalancing.
- **Redis Streams**: <2 ms p99 on a single node; XAUTOCLAIM & XPENDING give instant recovery without a separate broker.

## 3️⃣  Ordering Guarantees
- **Kafka**: Guarantees ordering per partition; you must shard your key space.
- **Redis Streams**: Strict ordering per stream key; no need to think about partitions.

## 4️⃣  Consumer Model
- **Kafka**: Consumer groups with offset commits; you need to manage consumer lag.
- **Redis Streams**: XREADGROUP + XAUTOCLAIM handles stalled consumers out of the box.

## 5️⃣  Use‑Case Fit
- **Kafka**: Heavy‑weight event sourcing, micro‑services at scale, multi‑region deployments.
- **Redis Streams**: Lightweight analytics, log aggregation, quick prototyping, and any scenario where you already run Redis.

## Bottom Line
If your stack already runs Redis and you need a low‑latency, low‑ops event log, Redis Streams win.  
If you’re building a globally distributed, fault‑tolerant event‑driven architecture with strict replay guarantees, Kafka is the go‑to.

*— Em*
```

SCRATCH_ADD: Added a quick comparison article on Redis Streams vs. Kafka for ForgeCore newsletter.