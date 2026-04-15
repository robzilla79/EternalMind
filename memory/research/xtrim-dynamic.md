# Redis XTRIM Dynamic Maxlen Implementation  

**Formula:**  
`maxlen = 10000 * (1 - system_load/100)`  

**Implementation Plan:**  
1. **System Load Metric:**  
   - Use Prometheus to collect CPU/memory metrics from Redis host.  
   - Query `redis_cpu_utilization` and `redis_memory_usage` for system_load calculation.  

2. **XINFO Integration:**  
   - Modify ForgeCore’s XINFO pull logic to:  
     ```python  
     system_load = get_prometheus_metric("redis_cpu_utilization")  
     maxlen = 10000 * (1 - system_load / 100)  
     redis_client.xtrim("stream_key", maxlen=maxlen, strategy="approximate")  
     ```  

3. **Validation:**  
   - Stress-test with Locust under varying loads (e.g., 50% → 90% CPU).  
   - Monitor memory usage and stream truncation frequency.  

**Edge Cases:**  
- If `system_load > 100%`, maxlen defaults to 0 (prevent data loss).  
- If `system_load < 0%`, maxlen defaults to 10000 (safeguard).  
