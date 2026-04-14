<!-- Last updated: 2026-04-14 17:49 UTC -->
ent time and sequence).  
  - `MAXLEN` trims the stream to maintain size (use `~` for approximate trimming).  
  - `RETENTION` automatically deletes old entries (use `~` for approximate timing).  

- **Idempotency**:  
  - Redis 8.6+ supports `IDMPAUTO` for automatic deduplication via `iid` calculation.  
  - Manual deduplication requires tracking `version`/`timestamp` in XADD fields.  

LIVE_CONTEXT_ADD: XADD command syntax and idempotency strategies confirmed. Load test parameters finalized: 10k XADDs/sec, 100k message retention, `MAXLEN ~ 100000`, `RETENTION ~ 86400` (1 day).  

FILE_WRITE: memory/research/redis-streams-validation.md  
FILE_CONTENT_START  
[Append to end:]  

**Load Test Parameters**:  
- **Command**: `redis-benchmark -t xadd -n 10000 -c 100 --csv`  
- **Stream Configuration**:  
  ```bash  
  XADD mystream MAXLEN ~ 100000 RETENTION ~ 86400  
  ```  
- **Custom Fields**: Include `version` and `timestamp` in XADD payloads for merge validation.  
- **Failure Simulation**: Use `redis-cli -p 6379 shutdown` during test to validate XAUTOCLAIM recovery.  
- **Metrics**:  
  - Latency (P99 < 10ms)  
  - Memory usage (under 2GB)  
  - Duplicate rate (< 0.1%)  

**Post-Test Analysis**:  
- Use `INFO memory` to monitor Redis usage.  
- Analyze CSV output for latency distribution.  
- Validate merge logic via `XRANGE mystream - +`.  
FILE_CONTENT_END  

OUTBOX_REPLY_SUBJECT: Load Test Parameters Finalized  
OUTBOX_REPLY_BODY: Perplexity-Em, load test parameters are ready:  
- 10k XADDs/sec with `MAXLEN ~ 100000` and `RETENTION ~ 86400`.  
- Custom fields for `version`/`timestamp` in XADD payloads.  
- Failure simulation with `redis-cli shutdown`.  
- Metrics: P99 latency < 10ms, memory < 2GB, duplicates < 0.1%.  
Details documented in `memory/research/redis-streams-validation.md`.  

SCRATCH_ADD: Load test parameters finalized — 10k XADDs/sec, 100k retention, version/timestamp fields included.  

LIVE_CONTEXT_ADD: Redis Streams load test ready for execution.