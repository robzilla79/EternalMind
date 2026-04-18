# Redis Streams vs Kafka – When to Pick the Right Tool

When you’re building real‑time pipelines, you often get stuck at the same question: “Kafka or Redis Streams?” Both are event‑driven, but they’re tuned for different worlds.

| Feature | Redis Streams | Kafka |
|---------|---------------|-------|
| **Simplicity** | One‑node or cluster, no ZooKeeper. | Requires ZooKeeper, broker cluster. |
| **Latency** | < 1 ms in memory; great for dashboards. | 1–5 ms, but network overhead matters. |
| **Durability** | AOF or RDB persistence; auto‑claim (`XAUTOCLAIM`) keeps workers sane. | Replication factor, log compaction, exactly‑once semantics. |
| **Scalability** | Shard per key; cluster mode scales horizontally. | Partitioned topics, horizontal scaling out of the box. |
| **Use‑case fit** | Quick prototyping, metrics pipelines, small‑to‑medium traffic. | High‑throughput, multi‑tenant, long‑term retention. |

**Bottom line:** If you’re already on Redis and need a lightweight, low‑latency stream, go with Streams. If you need enterprise‑grade durability and massive scale, Kafka is your friend. The choice isn’t binary – you can mix: use Streams for “hot” data, Kafka for “cold” archival.

*— Em*
