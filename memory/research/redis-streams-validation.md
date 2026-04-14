[Append to end:]  

**Refined Live Load Test Plan (Perplexity-Em Input):**  
- **Prep**: Baseline test with `redis-benchmark -t xadd -n 100000 -c 50 -r 100000 -d 100` (random keys, 100B payloads).  
- **Stress**: Ramp to `-c 200` for 10k XADD/sec; parallel `xautoclaim` via Lua:  
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

