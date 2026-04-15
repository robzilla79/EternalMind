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
