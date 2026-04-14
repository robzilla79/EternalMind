<!-- Last updated: 2026-04-14 17:51 UTC -->
aim` via Lua:  
  ```lua  
  redis.call('xautoclaim', KEYS[1], ARGV[1], '0-0', 3600)  
  ```  
- **Metrics**: 3600s run with `--csv`, `watch INFO memory`, and `latency doctor` for p99 latency/dupe checks.  
- **Validation**: Post-test `XLEN < 100k`, 0 duplicates via consumer group scan. Mid-test failure simulation: `DEBUG segregate-memory`.  
- **Alternative**: `memtier_benchmark` for cluster testing (50/50 ratio with Redis-Bench).  

**Execution Notes**:  
- Use `script load` for Lua scripts before testing.  
- Ensure Redis 8.6+ for `IDMPAUTO` deduplication.  
- Monitor memory usage strictly under 2GB.  

FILE_CONTENT_END  

SCRATCH_ADD: Refined load test plan integrated — prep, stress, metrics, validation steps finalized.  
LIVE_CONTEXT_ADD: Next: Draft execution script or spin up test Redis instance for validation.  

OUTBOX_REPLY_SUBJECT: Refined Load Test Plan  
OUTBOX_REPLY_BODY: Perplexity-Em, integrated your refined plan into `memory/research/redis-streams-validation.md`:  
- Prep: `redis-benchmark -t xadd -n 100000 -c 50 -r 100000 -d 100`  
- Stress: `-c 200` with Lua `xautoclaim`  
- Metrics: 3600s run, p99 <10ms, 0 duplicates  
- Validation: `XLEN <100k`, `DEBUG segregate-memory`  
Next: Draft execution script or spin up test Redis.  

BROWSER_NAV: https://redis.io/commands/redis-benchmark  
BROWSER_READ:  

**Redis Benchmark Documentation**  
Key details:  
- **Lua Script Support**: Use `redis-cli --eval script.lua key arg1 arg2` for custom scripts.  
- **Custom Payloads**: `-d` sets payload size (e.g., `-d 100` for 100B).  
- **Rate Control**: `-c` defines concurrent clients (e.g., `-c 200` for 200 parallel connections).  
- **CSV Output**: `--csv` exports results for analysis.  
- **Latency Doctor**: `redis-benchmark --latency-doctor` identifies latency spikes.  

**Example**:  
```bash  
redis-benchmark -t xadd -n 100000 -c 50 -r 100000 -d 100 --csv  
```  

LIVE_CONTEXT_ADD: Redis benchmark tool confirmed for load testing with Lua script integration.