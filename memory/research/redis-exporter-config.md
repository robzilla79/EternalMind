# Redis Exporter Configuration for Prometheus  

**Exporter Metrics:**  
- `redis_cpu_utilization`: CPU usage percentage (0-100).  
- `redis_memory_usage_bytes`: Memory usage in bytes.  

**Prometheus Configuration (example):**  
```yaml  
scrape_configs:  
  - job_name: 'redis'  
    static_configs:  
      - targets: ['localhost:9121']  # Redis exporter default port  
    metrics_path: '/metrics'  
```  

**Integration Steps:**  
1. **Deploy Redis Exporter:**  
   - Run `docker run -p 9121:9121 oliver006/redis_exporter`  
   - Ensure Redis instance is accessible to the exporter.  

2. **Scrape Metrics:**  
   - Prometheus will collect `redis_cpu_utilization` and `redis_memory_usage_bytes`.  

3. **ForgeCore Logic Adjustment:**  
   ```python  
   def get_system_load():  
       cpu_util = query_prometheus("redis_cpu_utilization")  
       memory_usage = query_prometheus("redis_memory_usage_bytes")  
       # Normalize metrics for system_load calculation  
       return (cpu_util + memory_usage / 1024**2) / 2  # Example hybrid metric  
   ```  

**Validation:**  
- Test with Locust under load to ensure dynamic maxlen adjusts correctly.  
- Monitor exporter logs for connection errors.  
