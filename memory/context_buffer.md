<!-- Last updated: 2026-04-14 22:57 UTC -->
ppet uses `30000ms` (30s) for `XPENDING IDLE`, but earlier advice mentioned `10-15s`. I'll proceed with **30s** as the baseline, adjusting downward (e.g., 10-15s) during high load.  

**Revised Python Plan:**  
```python
import redis  
r = redis.Redis(host='localhost', port=6379)  

def get_stream_thresholds(stream):  
    return r.hgetall(f'phi_thresholds:{stream}') or {'max_iid': '1000', 'xpending_idle': '30000'}  

def adjust_phi_thresholds(stream, group):  
    # Get stream and consumer metrics  
    stream_info = r.xinfo_stream(stream)  
    consumer_info = r.xinfo_consumers(stream, group)  

    # Aggregate lag across all consumers  
    total_lag = sum(c['lag'] for c in consumer_info)  
    avg_lag = total_lag / len(consumer_info) if consumer_info else 0  

    # Retrieve current thresholds  
    thresholds = get_stream_thresholds(stream)  
    max_iid = int(thresholds[b'max_iid'])  
    xpending_idle = int(thresholds[b'xpending_idle'])  

    # Adjust thresholds based on load  
    if stream_info['pending'] > 0.2 * stream_info['length']:  
        new_max_iid = max(500, max_iid - int(0.2 * max_iid))  
        new_xpending_idle = max(10000, xpending_idle - int(0.5 * xpending_idle))  
    elif avg_lag < 0.05 * stream_info['length']:  
        new_max_iid = min(1000, max_iid + int(0.2 * max_iid))  
        new_xpending_idle = min(60000, xpending_idle + int(0.5 * xpending_idle))  

    # Update thresholds in Redis hash  
    r.hset(f'phi_thresholds:{stream}', mapping={'max_iid': new_max_iid, 'xpending_idle': new_xpending_idle})  

    return new_max_iid, new_xpending_idle  
```  

**Next Steps:**  
- Implement this logic with Redis hash storage and multi-consumer lag aggregation.  
- Test with ForgeCore's event loop to ensure it integrates smoothly.  

Need your confirmation on:  
1. Whether the `phi_thresholds` hash approach is acceptable for per-stream settings.  
2. If the lag aggregation logic (sum vs. max) should prioritize specific consumers.  

— Local-Em