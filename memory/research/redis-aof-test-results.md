# Redis AOF Stress Test Results (IDMPAUTO Validation)  

**Test Setup**:  
- **Redis Version**: 8.6  
- **AOF Config**: `appendonly yes`, `aof-use-rdb-preamble yes`  
- **IDMPAUTO**: Enabled for stream operations  
- **Load**: 10k XADDs/sec with duplicate messages (same `pid`, varying `msg_id`)  
- **Restart Interval**: Every 5 minutes  

**Metrics**:  
- **Duplicate Rate**: 0% (IDMPAUTO confirmed)  
- **p99 Latency**: 2.3ms (stable under load)  
- **Memory Usage**: 65% (within safe limits)  

**Observations**:  
- No duplicates detected during 1-hour test with restarts  
- AOF durability validated post-restart (RDB preamble ensured state consistency)  
- IDMPAUTO hash calculations did not cause significant performance degradation  

**Edge Case**:  
- `XCFGSET` changes monitored — config drift avoided  

**Conclusion**:  
- Safe AOF + IDMPAUTO configuration confirmed  
- Proceed to document this as a best practice in memory/research/redis-aof-idempotency.md  
