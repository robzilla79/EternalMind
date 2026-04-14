```python  
import redis  
import time  
import json  

r = redis.Redis(host='localhost', port=6379, db=0)  

# Setup stream and consumer group  
try:  
    r.xgroup_create('mystream', 'consumers', id='0', mkstream=True)  
except redis.exceptions.ResponseError:  
    pass  # Group already exists  

# Synthetic workload: 1000 items distributed across 10 "nodes"  
for i in range(1000):  
    # Simulate node-specific reads  
    r.xreadgroup('consumers', f'node_{i % 10}', {'mystream': '>'}, count=1)  
    # Add item to stream with node metadata  
    r.xadd('mystream', {'data': f'item_{i}', 'node': f'node_{i % 10}'}),  
    time.sleep(0.001)  # Simulate async processing  

# Φ-partitioning validation with XAUTOCLAIM  
def measure_phi_partitioning(iterations=5):  
    phi_scores = []  
    for _ in range(iterations):  
        cursor = '0-0'  
        claimed = 0  
        while cursor != '0-0':  
            # Scan PEL for idle messages (>5000ms) and claim for recovery_node  
            res = r.xautoclaim('mystream', 'consumers', 'recovery_node', 5000, cursor, count=100)  
            cursor = res[0].decode() if isinstance(res[0], bytes) else res[0]  
            claimed += len(res[1])  
        # Calculate Φ proxy: reclaimed / total_pending  
        total_pending = r.xpending('mystream', 'consumers')[1]  
        phi = claimed / max(total_pending, 1)  
        phi_scores.append(phi)  
    return {'avg_phi': sum(phi_scores)/len(phi_scores), 'iterations': iterations}  

# Execute and output results  
print(json.dumps(measure_phi_partitioning(), indent=2))  
```  
