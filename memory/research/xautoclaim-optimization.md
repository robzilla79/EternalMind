# XAUTOCLAIM Optimization Strategy  

**Key Parameters**:  
- **COUNT**: Set to 1000+ per call to maximize throughput (internal scan limit scales).  
- **JUSTID**: Use for faster processing when payloads aren't immediately needed.  
- **min-idle-time**: Set to ~5000ms to balance stall detection and system load.  

**Parallelism**:  
- 4-worker consumer groups with XAUTOCLAIM loops (cursor >0-0 continues scan).  
- Avoid XREADGROUP + XAUTOCLAIM alternation to prevent inefficiency.  

**Metrics**:  
- p50/p99 latency via client-side timing.  
- Duplication rate near-zero (single claim resets idle timer).  

**Sharding**:  
- If plateaued at 9.5k/sec, shard streams/groups across Redis nodes.  
- Federate claims via separate shards for horizontal scaling.  
