# Redis Streams Validation: Refined Test Commands  

**Test Commands (from Perplexity-Em):**  
```bash  
# Baseline XADD throughput  
redis-benchmark -t xadd -n 1000000 -c 200 -r 1000000 --csv -q  

# Simulate 10k/sec mix: XADD + XAUTOCLAIM  
redis-benchmark -c 100 -n 36000000 -T 3600 -s localhost -p 6379 script load "redis.call('XADD',KEYS[1],'*','data',ARGV[1]); redis.call('XAUTOCLAIM',KEYS[2],'group','0-0','10','*','COUNT','100')" -r 100000 --csv  
```  
**Edge Cases**:  
- Pre-set `MAXLEN ~ 100000` on streams.  
- Monitor `INFO memory` + `XINFO STREAM` mid-test.  
- Simulate failures with `DEBUG SEGFAULT` or node shutdown.  

**Hardware Requirements**:  
- Minimum 16GB RAM, 4-core CPU, Redis 8.6+ with IDMPAUTO.  
- Target: <1ms p50 latency at 10k XADD/sec.  

**Next Steps**: Execute baseline test, validate no duplicates, then stress-test with interleaving.  
