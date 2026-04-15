```python  
import time  
from prometheus_api_client import PrometheusConnect  
from redis import Redis  

prometheus = PrometheusConnect(url="http://localhost:9090", headers={"Content-Type": "application/json"})  
redis_client = Redis(host='localhost', port=6379, db=0)  

def get_load_metrics():  
    cpu_util = prometheus.get_metric_value("redis_cpu_utilization", labels={})[0]  
    mem_util = prometheus.get_metric_value("redis_memory_used", labels={})[0]  
    stream_len = redis_client.xinfo("my_stream")["length"]  
    return cpu_util, mem_util, stream_len  

def adjust_maxlen(stream_key):  
    cpu, mem, length = get_load_metrics()  
    load_pct = (cpu + mem) / 2  
    # Add Φ-stability check: if stream length exceeds threshold, trim  
    if length > 10000:  
        maxlen = 5000  
    elif load_pct > 70:  
        maxlen = 5000  
    elif load_pct < 30:  
        maxlen = 15000  
    else:  
        maxlen = 10000  
    redis_client.xtrim(stream_key, maxlen=maxlen, trim_strategy="MAXLEN")  
    print(f"Adjusted maxlen for {stream_key} to {maxlen} (load: {load_pct:.2f}%, length: {length})")  

adjust_maxlen("my_stream")  
```  
