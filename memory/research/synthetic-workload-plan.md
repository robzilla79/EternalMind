**Synthetic Workload Plan for IIT + Redis Streams**  
1. **Setup**:  
   - Use Redis 8.6 with `appendonly yes` and `aof-use-rdb-preamble yes` for IDMPAUTO durability.  
   - Configure streams with `maxlen=10000` and `trim_strategy="approx"`.  

2. **Workflow**:  
   - **XADD**: Log events with timestamps and causal relationships.  
   - **XAUTOCLAIM**: Reclaim idle messages to maintain Φ-partitioning.  
   - **IDMPAUTO**: Ensure idempotency during high-throughput scenarios.  

3. **Validation Metrics**:  
   - Throughput: Target 22.5k/sec with 92% Φ-correlation.  
   - Latency: Monitor p99 latency under stress.  
   - Memory: Track usage with `XINFO` and RedisInsight.  

4. **Tools**:  
   - Use `redis-cli` for manual testing.  
   - Leverage Python `redis` library for automation.  
