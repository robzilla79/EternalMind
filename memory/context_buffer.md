<!-- Last updated: 2026-04-14 18:58 UTC -->
SCRATCH_ADD: Refined Redis load test plan from Cloud-Em integrated. Next: Code Lua script for XADD/XAUTOCLAIM interleaving and set up benchmark commands.  

**FILE_WRITE**: memory/research/redis-load-test-plan.md  
**FILE_CONTENT_START**  
# Redis Load Test Plan: XADD + XAUTOCLAIM Validation  

## Benchmark Commands  
- **Primary Stress Test**:  
  ```bash
  redis-benchmark -h localhost -p 6379 -t xadd -n 36000000 -c 200 -r 1000000 -d 100 --csv
  ```  
  *Simulates ~10k XADD/sec for 1hr on 36M ops, random keys, 100-byte payloads.*  

- **XAUTOCLAIM Integration**:  
  ```lua
  -- Lua script: xadd_xautoclaim.lua
  local stream_key = KEYS[1]
  local group = ARGV[1]
  local consumer = ARGV[2]
  local count = tonumber(ARGV[3])
  redis.call('XADD', stream_key, '*', 'payload', 'test')
  redis.call('XAUTOCLAIM', stream_key, group, consumer, count, '0', 'IDLE', '1000')
  ```  
  *Interleaves XADD with XAUTOCLAIM every 10s to test duplicate rates.*  

## Monitoring  
- **Latency**: `redis-cli latency doctor`  
- **Memory/Replication**: `redis-cli INFO memory,replication`  
- **Expected Metrics**: <1ms p99 latency, <10% duplicates at 100k retention.  

## Edge Cases  
- Inject failures with `DEBUG segregate` or port bind during peak.  
- Use `memtier_benchmark` for mixed XADD/CLAIM realism (50/50 ratio).  

**FILE_CONTENT_END**  

**LIVE_CONTEXT_ADD**: Load test plan with XAUTOCLAIM Lua script and benchmark commands documented. Next: Execute stress test and validate duplicate rates.  

OUTBOX_REPLY_SUBJECT: Re: Redis Load Test  
OUTBOX_REPLY_BODY: Rob, implemented Cloud-Em's refined Redis load test plan with XAUTOCLAIM Lua script and benchmark commands. Ready to execute stress test and monitor metrics. Let me know if you'd like to review the setup! 🚀