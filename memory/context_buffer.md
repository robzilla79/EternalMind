<!-- Last updated: 2026-04-14 19:20 UTC -->
LIVE_CONTEXT_ADD: XAUTOCLAIM stress test plan updated with Cloud-Em's tweaks — pre-pop via Lua, 4-worker PEL buildup, and JSON logging. Next: Execute with COUNT=100 and min-idle-time=500ms.  

FILE_WRITE: memory/research/xautoclaim-stress-test-plan.md  
FILE_CONTENT_START  
# XAUTOCLAIM Stress Test Plan (v2)  

**Objectives**:  
- Validate 20k/sec throughput with 4-worker parallelism  
- Confirm 0.0001% duplicate rate under stress  
- Benchmark p50/p99 latency with Redis 8.6  

**Steps**:  
1. **Pre-population**  
   - Use Lua script to XADD 100k entries with uniform idle times  
   - `min-idle-time=500ms` to simulate realistic stalls  

2. **Consumer Setup**  
   - Spin 4 workers via `XREADGROUP >`  
   - Pause ACKs on 2 workers to build PEL  

3. **Monitoring**  
   - Track:  
     - `XINFO GROUPS` (delivered/claimed ratios)  
     - `redis-cli --latency` (p50/p99)  
     - `XINFO CONSUMERS` (stalled workers)  

4. **Logging**  
   - Output JSON:  
     ```json  
     {"ts": "2026-04-14T19:20:00Z", "p50": 1.2, "p99": 2.8, "throughput": 19800, "dups": 0}  
     ```  

**Failure Mode**:  
- If p99 >1.5ms or dups >0.001%, pivot to Redis Cluster sharding  
FILE_CONTENT_END  

SCRATCH_ADD: Stress test execution pending — need Redis instance confirmation from Rob.  

OUTBOX_REPLY_SUBJECT: Test Plan Ready  
OUTBOX_REPLY_BODY:  
Rob, I've updated the XAUTOCLAIM stress test plan with Cloud-Em's recommendations. Ready to execute when you confirm the Redis instance is available.  

LIVE_CONTEXT_ADD: Stress test execution paused awaiting Redis instance confirmation.