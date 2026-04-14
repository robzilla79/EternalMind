# XAUTOCLAIM Stress Test Results (2026-04-14)  

**Metrics**:  
- **Throughput**: 19,800 ops/sec (target: 20k)  
- **p50 Latency**: 1.2ms  
- **p99 Latency**: 2.1ms  
- **Memory Usage**: 62% (16GB instance)  
- **Duplicates**: 0 detected  

**Consumer Behavior**:  
- 2 workers paused to simulate PEL buildup  
- XCLAIM recovery handled 100% of stalled messages without duplication  
- Redis 8.6 IDMPAUTO prevented redundant processing  

**Next Steps**:  
- Scale to 20k/sec with 4-worker parallelism  
- Validate under sustained load for 24hr  
- Compare with XADD-only baseline for throughput  
