```python  
import redis  
import time  

r = redis.Redis(host='localhost', port=6379, db=0)  

# Create consumer group if not exists  
try:  
    r.xgroup("CREATE", "causal_stream", "consumer_group", "0")  
except redis.exceptions.ResponseError:  
    pass  # Group already exists  

# XADD with maxlen and trim_strategy  
r.xadd('causal_stream', {'event': 'node_a', 'timestamp': time.time()}, maxlen=10000, trim_strategy='approx')  

# XAUTOCLAIM for message recovery  
r.xautoclaim('causal_stream', 'consumer_group', 'consumer_name', 1000, 'JUSTID')  

# IDMPAUTO deduplication (implicit via Redis 8.6)  
r.xadd('causal_stream', {'event': 'node_b', 'timestamp': time.time()})  
```  
