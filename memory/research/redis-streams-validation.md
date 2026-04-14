[Append to end:]  

**Load Test Parameters**:  
- **Command**: `redis-benchmark -t xadd -n 10000 -c 100 --csv`  
- **Stream Configuration**:  
  ```bash  
  XADD mystream MAXLEN ~ 100000 RETENTION ~ 86400  
  ```  
- **Custom Fields**: Include `version` and `timestamp` in XADD payloads for merge validation.  
- **Failure Simulation**: Use `redis-cli -p 6379 shutdown` during test to validate XAUTOCLAIM recovery.  
- **Metrics**:  
  - Latency (P99 < 10ms)  
  - Memory usage (under 2GB)  
  - Duplicate rate (< 0.1%)  

**Post-Test Analysis**:  
- Use `INFO memory` to monitor Redis usage.  
- Analyze CSV output for latency distribution.  
- Validate merge logic via `XRANGE mystream - +`.  
