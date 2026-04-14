[Append to end:]  

**Live Load Test Plan**:  
- **Tools**: Use `redis-benchmark` with custom Lua scripts to simulate concurrent XADD/XAUTOCLAIM operations.  
- **Scenario**: 10k XADDs/sec for 1 hour, 100k message retention window.  
- **Metrics**: Track latency, memory usage, and duplicate rate under stress.  
- **Validation**: Confirm XAUTOCLAIM handles 100% of idle messages without duplication.  
