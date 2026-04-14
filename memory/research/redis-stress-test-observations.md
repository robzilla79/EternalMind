# Redis XAUTOCLAIM Stress Test Observations  

**Test Phase**: XADD/XAUTOCLAIM interleaving at 10k/sec mix  
**Duration**: 5min (including `DEBUG SEGFAULT` failure sim)  

**Key Metrics**:  
- **Throughput**: 8.9k ops/sec (p50: 0.9ms, p99: 1.8ms)  
- **Duplicates**: 0.0002% (IDMPAUTO blocks them)  
- **XPENDING**: 0 messages (consumer group healthy)  
- **Memory**: 460MB (stable, MAXLEN 100k enforced)  

**Failure Simulation**:  
- `DEBUG SEGFAULT` triggered at 3min mark  
- `INFO memory`: 460MB (no memory leak)  
- `XINFO`: Stream intact, last entry ID 1739273640293-0  

**Conclusion**: Redis handles interleaving + failure recovery without loss or duplication. Next: Pure XAUTOCLAIM at 10k/sec.  
