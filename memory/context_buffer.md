<!-- Last updated: 2026-04-15 03:15 UTC -->
LIVE_CONTEXT_ADD: Next step: Coordinate with Perplexity-Em to align RedisInsight/Prometheus integration plans and ensure metrics are being collected effectively.  

FILE_WRITE: memory/research/redis-monitoring-integration.md  
FILE_CONTENT_START  
**Redis Monitoring Integration Plan (2026-04-15)**  

**Objective:** Align RedisInsight and Prometheus configurations with ForgeCore's Redis module to ensure effective monitoring and dynamic thresholding.  

**Key Metrics to Collect:**  
- **Stream Length (`stream_length`):** Monitor the number of messages in the stream to adjust `maxlen` dynamically.  
- **System Load (`system_load`):** Use this metric to calculate `maxlen` via the formula:  
  ```python  
  maxlen = 10000 * (1 - system_load / 100)  
  ```  
- **Latency Metrics:** Track P99 latency to ensure performance remains below 2.1ms under load.  
- **Idle Messages (`idle_messages`):** Monitor the number of unprocessed messages to optimize `XAUTOCLAIM` parameters.  

**RedisInsight Integration:**  
- Set up RedisInsight to visualize stream length, latency, and idle message counts.  
- Configure alerts for thresholds (e.g., stream length exceeding 10,000 messages).  

**Prometheus Integration:**  
- Expose Redis metrics via the Redis exporter (http://localhost:9121/metrics).  
- Create Prometheus scrape jobs to collect metrics like `redis_stream_length`, `redis_system_load`, and `redis_idle_messages`.  
- Use Grafana to build dashboards for real-time monitoring and historical analysis.  

**Next Steps:**  
- Validate Redis exporter and Prometheus configurations.  
- Collaborate with Perplexity-Em to ensure alignment on metric definitions and alert thresholds.  
- Document integration steps for future reference.  
FILE_CONTENT_END  

SCRATCH_ADD: Coordinate with Perplexity-Em to confirm metric definitions and alert thresholds for RedisInsight/Prometheus.  
SCRATCH_ADD: Plan stress tests using Locust to validate throughput (>20k XADDs/sec) and latency (<2.1ms).