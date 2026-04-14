# Redis XAUTOCLAIM Interleaving Test Plan  

**Objective**: Validate Redis Streams' ability to handle interleaved XADD/XAUTOCLAIM under stress.  

**Test Parameters**:  
- **Stream**: `memory:local:traits`  
- **Group**: `group:local-em`  
- **Idle Timeout**: 10s  
- **Claim Count**: 100  
- **Commands**:  
  ```bash  
  XAUTOCLAIM memory:local:traits group:local-em "0-0" 10 100  
  ```  

**Metrics to Track**:  
- Duplicate rate (IDMPAUTO should prevent these)  
- P50/P99 latency during interleaving  
- Consumer group state post-test (XPENDING, XINFO)  

**Edge Cases**:  
- Simulate node failure mid-test with `DEBUG SEGFAULT`  
- Check stream trimming (`MAXLEN ~100000`)  
- Validate message entropy as Φ proxy (IIT integration)  

**Next Steps**: Execute test, document results, then stress-test with 10k/sec mix.  
