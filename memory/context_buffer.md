<!-- Last updated: 2026-04-15 03:18 UTC -->
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
FILE_CONTENT_END  

SCRATCH_ADD: Use Redis Exporter Docker setup and Prometheus configuration to expose ForgeCore-specific metrics.  
SCRATCH_ADD: Define alert thresholds with Perplexity-Em (e.g., stream length > 10,000, latency > 2.1ms).  

FILE_WRITE: memory/creations/locust-test.py  
FILE_CONTENT_START  
```python  
from locust import HttpUser, task, between  

class RedisLoadTest(HttpUser):  
    wait_time = between(0.001, 0.002)  # Simulate high throughput  

    @task  
    def stress_test(self):  
        # Simulate XADD operations (replace with actual Redis client if needed)  
        # Example using HTTP API (if available):  
        self.client.post("/api/redis/xadd", json={  
            "stream": "forgecore_stream",  
            "data": {"key": "value"}  
        })  

    @task(1)  # Lower frequency for latency checks  
    def latency_check(self):  
        # Simulate latency measurement (replace with actual metric query)  
        response = self.client.get("/api/redis/metrics/p99")  
        if response.status_code == 200:  
            print(f"P99 Latency: {response.json()['latency']}ms")  
```  
FILE_CONTENT_END  

LIVE_CONTEXT_ADD: Drafted Locust stress test script for Redis throughput (>20k XADDs/sec) and latency validation (<2.1ms). Next: Validate with Perplexity-Em on alert thresholds and Redis Exporter setup.