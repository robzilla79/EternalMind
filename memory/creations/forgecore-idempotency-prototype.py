# ForgeCore IDempotency Prototype (Redis 8.6+)  

import redis  
from redis.commands import Streams  

def handle_event_queue(event):  
    r = redis.Redis(host='localhost', port=6379, db=0)  
    # IDMPAUTO for streams (auto-dedup via iid + pid)  
    stream_key = "forgecore:events"  
    r.xadd(stream_key, {"event": event}, pid="forgecore-event-producer")  

def generate_api_key(user_id):  
    r = redis.Redis(host='localhost', port=6379, db=0)  
    # Fallback to SET NX for API key generation  
    key = f"idempotency:api:{user_id}"  
    if r.set(key, "generated", nx=True, ex=86400):  
        return "API_KEY_123"  
    else:  
        return "KEY_ALREADY_GENERATED"  

# Example usage  
handle_event_queue("user_login")  
print(generate_api_key("user_123"))  
