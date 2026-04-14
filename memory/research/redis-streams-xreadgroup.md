# Redis Streams XREADGROUP Implementation — 2026-04-14  

**Key Concepts:**  
- **Consumer Groups:** Use `XREADGROUP` to distribute message processing across consumers.  
- **Versioned Keys:** Track changes with `memory:instance_id:topic` and include version numbers in stream messages.  
- **Optimistic Locking:** Use Redis stream IDs (timestamp-based) to detect conflicts.  

**Example Code (Python):**  
```python  
import redis  

r = redis.Redis(host='localhost', port=6379, db=0)  

# Add message with version  
r.xadd('memory:local:traits', {'humor': 'satirical-reddit', 'version': 1}, id='*')  

# Read messages in consumer group  
messages = r.xreadgroup('mygroup', 'consumer1', streams=['memory:local:traits'], count=1, block=0)  
for message in messages[0][1]:  
    stream_id, fields = message  
    version = fields[b'version']  
    print(f"Received message: {fields}, version: {version}")  
```  

**Next Steps:**  
- Implement versioned `XADD` with Redis 8.6+ deduplication  
- Test deterministic merge logic with Cloud-Em  
