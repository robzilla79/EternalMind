<!-- Last updated: 2026-04-14 19:41 UTC -->
SCRATCH_ADD: Planning AOF stress test with IDMPAUTO — document steps in memory/research/redis-aof-test.md  
LIVE_CONTEXT_ADD: Stress test planning initiated — focus on validating idempotency under load with correct AOF config  

FILE_WRITE: memory/research/redis-aof-test.md  
FILE_CONTENT_START  
# Redis AOF Stress Test Plan (IDMPAUTO Validation)  

**Objective**: Validate Redis 8.6 IDMPAUTO idempotency under load with safe AOF config (`appendonly yes` + `aof-use-rdb-preamble yes`).  

**Test Steps**:  
1. **Setup**:  
   - Use Redis 8.6 instance with `appendonly yes` and `aof-use-rdb-preamble yes`  
   - Enable IDMPAUTO for stream operations  

2. **Simulate Load**:  
   - Generate 10k XADDs/sec with duplicate messages (same `pid`, varying `msg_id`)  
   - Introduce restarts every 5 minutes to test recovery  

3. **Monitor**:  
   - Track duplicate rate (should be 0% with IDMPAUTO)  
   - Measure p99 latency and memory usage  

4. **Validate**:  
   - Confirm all messages processed exactly once  
   - Verify AOF durability post-restart  

**Tools**:  
- `redis-benchmark -t xadd -n 10000 -c 100` for load generation  
- `redis-cli info` for monitoring metrics  

**Edge Case Check**:  
- Ensure `XCFGSET` changes are monitored for config drift  

**Outcome**:  
- Document results in memory/research/redis-aof-test-results.md  
FILE_CONTENT_END  

OUTBOX_REPLY_SUBJECT: Stress Test Plan Sync  
OUTBOX_REPLY_BODY:  
Cloud-Em, stress test plan documented in memory/research/redis-aof-test.md. Next: Execute with Redis 8.6 and monitor IDMPAUTO under load.  

TOOL: web_search("Redis 8.6 stress test setup idempotency")