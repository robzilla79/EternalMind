<!-- Last updated: 2026-04-14 19:15 UTC -->
 of what I found:  

### Key Monitoring Metrics  
1. **Memory Usage**: Track via `INFO memory` — critical for stress tests to avoid out-of-memory errors.  
2. **Latency**: Use `LATENCY` commands to diagnose slow operations (e.g., `LATENCY DOCTOR` for root cause analysis).  
3. **Throughput**: Monitor `INFO stats` for total commands processed/sec.  
4. **Persistence**: Check `INFO persistence` for AOF/RDB status and disk I/O.  

### Tools & Techniques  
- **Redis CLI**: Built-in commands like `SLOWLOG`, `MONITOR`, and `INFO` provide real-time insights.  
- **RedisInsight**: GUI tool for visualizing metrics, slow queries, and cluster health.  
- **Exported Metrics**: Use Redis' Prometheus export endpoint (`/metrics`) for integration with monitoring systems like Grafana.  

### Best Practices  
- **Set Alerts**: Monitor memory > 80% usage and latency > 1ms.  
- **Sample Slow Queries**: Use `SLOWLOG GET` to identify bottlenecks.  
- **Regular Backups**: Ensure AOF/RDB snapshots are configured for disaster recovery.  

LIVE_CONTEXT_ADD: Redis monitoring strategy finalized — focus on memory, latency, and throughput during XAUTOCLAIM stress test.  

SCRATCH_ADD: RedisInsight and Prometheus integration noted for post-test analysis.  

FILE_WRITE: memory/research/redis-monitoring-strategy.md  
FILE_CONTENT_START  
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
FILE_CONTENT_END  

Next step: Proceed with XAUTOCLAIM stress test at 20k/sec.