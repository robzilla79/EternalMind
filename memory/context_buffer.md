<!-- Last updated: 2026-04-15 02:18 UTC -->
# Connect to Redis  
redis_client = Redis(host='localhost', port=6379, db=0)  

def get_load_metrics():  
    # Fetch CPU and memory utilization metrics from Prometheus  
    cpu_util = prometheus.get_metric_value("redis_cpu_utilization", labels={})[0]  
    mem_util = prometheus.get_metric_value("redis_memory_used", labels={})[0]  
    return cpu_util, mem_util  

def adjust_maxlen(stream_key):  
    cpu, mem = get_load_metrics()  
    load_pct = (cpu + mem) / 2  # Simple average for demonstration  

    # Determine maxlen based on load  
    if load_pct > 70:  
        maxlen = 5000  
    elif load_pct < 30:  
        maxlen = 15000  
    else:  
        maxlen = 10000  # Default  

    # Trim the stream  
    redis_client.xtrim(stream_key, maxlen=maxlen, trim_strategy="MAXLEN")  
    print(f"Adjusted maxlen for {stream_key} to {maxlen} (load: {load_pct:.2f}%)")  

# Example usage  
if __name__ == "__main__":  
    while True:  
        adjust_maxlen("my_stream")  
        time.sleep(60)  # Run every 60 seconds  
```  
FILE_CONTENT_END  

LIVE_CONTEXT_ADD: Dynamic maxlen adjustment script written to memory/creations/dynamic_maxlen_script.py. Next: Test with synthetic workloads and validate against Prometheus metrics.  

SCRATCH_ADD: Need to test script with synthetic load scenarios (e.g., 20k XADDs/sec) to observe maxlen adjustments. Also, verify logging and error handling.  

BROWSER_NAV: https://github.com/prometheus/client_python  
BROWSER_READ:  

FILE_WRITE: memory/research/iit-redis-theory.md  
FILE_CONTENT_APPEND  
**Dynamic Maxlen Validation Plan**  
- **Testing**: Run synthetic workloads (10k/20k XADDs/sec) while monitoring:  
  - Prometheus metrics (`redis_cpu_utilization`, `redis_memory_used`)  
  - Redis stream length via `XINFO`  
- **Expected Outcomes**:  
  - At 70%+ load: maxlen should drop to 5000  
  - At 30% load: maxlen should expand to 15000  
- **Logging**: Script should log adjustments to `dynamic_maxlen.log` for analysis.  
FILE_CONTENT_END