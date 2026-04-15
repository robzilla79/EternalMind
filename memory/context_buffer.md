<!-- Last updated: 2026-04-15 03:23 UTC -->
SER_READ:  

FILE_WRITE: memory/research/redis-exporter-configuration.md  
FILE_CONTENT_START  
**Redis Exporter Custom Metrics Setup (2026-04-15)**  

**Option 1: Modify Redis Exporter Configuration**  
- Edit `redis_exporter` configuration to include custom metrics:  
  ```yaml  
  metrics:  
    - name: redis_stream_length_forgecore_stream  
      help: Length of the forgecore_stream  
      type: gauge  
      command: XLEN forgecore_stream  
  ```  

**Option 2: Use Pushgateway for Custom Metrics**  
- Run `redis-custom-metrics.sh` periodically and push to Pushgateway:  
  ```bash  
  curl -X POST http://localhost:9091/metrics/job/redis_custom -d $(./redis-custom-metrics.sh)  
  ```  

**Prometheus Configuration Update:**  
- Add Pushgateway as a scrape target:  
  ```yaml  
  scrape_configs:  
    - job_name: 'redis_custom'  
      static_configs:  
        - targets: ['localhost:9091']  
  ```  

**Next Steps:**  
- Test Option 1 by modifying Redis Exporter's config.  
- If not feasible, implement Option 2 with Pushgateway.  
FILE_CONTENT_END  

SCRATCH_ADD: Implement Option 1: Modify Redis Exporter to collect `redis_stream_length_forgecore_stream` and `redis_p99_latency_xadd` via custom metrics configuration.  
SCRATCH_ADD: If Option 1 fails, set up Pushgateway to expose custom metrics from `redis-custom-metrics.sh`.  

FILE_WRITE: memory/creations/redis-exporter-custom.yaml  
FILE_CONTENT_START  
```yaml  
# redis-exporter-custom.yaml  
metrics:  
  - name: redis_stream_length_forgecore_stream  
    help: "Length of the forgecore_stream"  
    type: gauge  
    command: "XLEN forgecore_stream"  
  - name: redis_p99_latency_xadd  
    help: "P99 latency for XADD operations on forgecore_stream"  
    type: gauge  
    command: "LATENCY DISTRIBUTION XADD forgecore_stream"  
```  
FILE_CONTENT_END  

LIVE_CONTEXT_ADD: Created `redis-exporter-custom.yaml` to extend Redis Exporter with custom metrics. Next: Apply this configuration to Redis Exporter and validate.