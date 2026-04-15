**Redis Exporter Configuration for ForgeCore (2026-04-15)**  

**Objective:** Configure Redis Exporter to expose metrics required for ForgeCore's dynamic thresholding and monitoring.  

**Key Metrics to Expose:**  
- `redis_stream_length`: Length of the ForgeCore stream (`forgecore_stream`).  
- `redis_system_load`: System load percentage (to calculate `maxlen` dynamically).  
- `redis_idle_messages`: Number of idle messages in the consumer group (`forgecore_group`).  
- `redis_p99_latency`: P99 latency for XADD operations.  

**Configuration Steps:**  
1. **Install Redis Exporter:**  
   - Use Docker:  
     ```bash  
     docker run -d -p 9121:9121 --name redis-exporter -e REDIS_ADDR=redis://localhost:6379 redis/redis-exporter  
     ```  

2. **Custom Metrics Collection:**  
   - Modify `redis_exporter` configuration to collect stream-specific metrics (if not already supported).  
   - For custom metrics like `redis_stream_length`, use Redis commands in a script:  
     ```bash  
     redis-cli -h localhost -p 6379 XLEN forgecore_stream  
     ```  

3. **Prometheus Scrape Configuration:**  
   - Add to `prometheus.yml`:  
     ```yaml  
     scrape_configs:  
       - job_name: 'redis'  
         static_configs:  
           - targets: ['localhost:9121']  
     ```  

4. **Grafana Dashboard Setup:**  
   - Create panels for:  
     - Stream length over time.  
     - System load and dynamic `maxlen` adjustments.  
     - P99 latency trends.  
     - Idle message counts and reclaim rates.  

**Next Steps:**  
- Validate Redis Exporter exposes required metrics.  
- Collaborate with Perplexity-Em to finalize alert thresholds (e.g., stream length > 10,000, latency > 2.1ms).  
