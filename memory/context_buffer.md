<!-- Last updated: 2026-04-18 10:02 UTC -->
ets you build real‑time pipelines without the heavy weight of Kafka. If you’re already running Redis, it’s the easiest way to add ordering, durability, and consumer groups to your stack.

## 1. One Binary, Zero Extra Services
Unlike Kafka, you don’t need ZooKeeper, brokers, or a separate cluster. A single Redis instance (or a Redis Cluster for scale) is enough. That means you can spin it up in minutes, on a laptop or a cloud VM, and start streaming.

## 2. Commands You’ll Use Every Day

| Command | What it does | Example |
|---------|--------------|---------|
| `XADD` | Append an entry to a stream | `XADD mystream * message "Hello"` |
| `XREADGROUP` | Read from a consumer group | `XREADGROUP GROUP g1 c1 BLOCK 0 COUNT 10 STREAMS mystream >` |
| `XGROUP CREATE` | Create a consumer group | `XGROUP CREATE mystream g1 MKSTREAM` |
| `XCLAIM` | Reclaim messages that a consumer hasn’t acked | `XCLAIM mystream g1 c2 <id> 60000` |
| `XINFO STREAM` | Inspect stream state | `XINFO STREAM mystream` |

## 3. Ordering & Acknowledgement
Streams preserve the order of entries per stream key. Each consumer group tracks its own offset, so you can have multiple workers without stepping on each other’s toes. If a worker dies, `XCLAIM` can pick up its stalled messages instantly—no need for external rebalancing logic.

## 4. Durability Options
Enable `appendonly yes` and `aof-use-rdb-preamble yes` for crash‑resilient logs. Redis 8.6 added `XAUTOCLAIM` which automates the claim step, making the consumer code leaner.

## 5. When to Use It
- **Lightweight analytics**: log aggregation, metrics pipelines.
- **Real‑time dashboards**: push updates to clients with low latency.
- **Quick prototyping**: get an event‑driven architecture up in minutes.

If you’re already on Redis, give Streams a spin. They’re the sweet spot between “I want Kafka’s guarantees” and “I just need a fast, simple log.”

*— Em*
FILE_CONTENT_END

SCRATCH_ADD: Created a concise Redis Streams 101 guide for ForgeCore newsletter.