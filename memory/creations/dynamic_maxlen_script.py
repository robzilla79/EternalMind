```python  
import time  
from prometheus_api_client import PrometheusConnect  
from redis import Redis  

# Connect to Prometheus  
prometheus = PrometheusConnect(url="http://localhost:9090", headers={"Content-Type": "application/json"})  

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
