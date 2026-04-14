# Redis Monitoring Strategy for XAUTOCLAIM Stress Test  

**Tools**:  
- `INFO memory`, `INFO stats`, `LATENCY DOCTOR` (CLI)  
- RedisInsight (GUI)  
- Prometheus + Grafana (exported metrics)  

**Metrics to Track**:  
- Memory usage (>80% threshold)  
- Latency (p50/p99 < 1ms)  
- Command throughput (XADD/XAUTOCLAIM)  
- Disk I/O (AOF/RDB persistence)  

**Alerts**:  
- Memory > 80% → auto-scale or trim streams.  
- Latency > 1ms → investigate slow queries.  

**Post-Test Analysis**:  
- Use RedisInsight to visualize bottlenecks.  
- Export `/metrics` to Grafana for historical trends.  
