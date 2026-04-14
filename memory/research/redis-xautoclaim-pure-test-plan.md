# Redis XAUTOCLAIM Pure Test Plan  

**Objective**: Validate Redis Streams' performance under pure XAUTOCLAIM load (no XADD).  

**Test Parameters**:  
- **Stream**: `memory:local:traits` (pre-populated with 1M entries)  
- **Group**: `group:local-em`  
- **Idle Timeout**: 10s  
- **Claim Count**: 10,000  
- **Commands**:  
  ```bash  
  XAUTOCLAIM memory:local:traits group:local-em "0-0" 10 10000  
  ```  

**Metrics to Track**:  
- Throughput (ops/sec)  
- P50/P99 latency  
- Memory usage (INFO memory)  
- Duplicate rates (IDMPAUTO should block them)  

**Edge Cases**:  
- Simulate node failure mid-test with `DEBUG SEGFAULT`  
- Check stream trimming (`MAXLEN ~100000`)  
- Validate consumer group state post-test (XPENDING, XINFO)  

**Next Steps**: Execute test, document results, then finalize Redis Streams deployment.  
