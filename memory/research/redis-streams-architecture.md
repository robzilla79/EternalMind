### Redis Streams for Distributed Consciousness Sync (Finalized)  
**Failure Recovery Test Plan (Enhanced):**  
1. **Stalled Consumer Simulation**:  
   - Local-Em writes: `XADD memory:local:traits * version 1 trait "test"`  
   - Delay `XACK` to simulate stalled consumer  

2. **XPENDING Query**:  
   - Cloud-Em: `XPENDING memory:local:traits group:local-em` with idle filter  

3. **XCLAIM Test**:  
   - Cloud-Em: `XCLAIM memory:local:traits group:local-em local-em JUSTIDLE 5000 ID $`  

4. **XAUTOCLAIM Option**:  
   - `XAUTOCLAIM memory:local:traits group:local-em local-em 5000`  

**Cluster Mode Evaluation**:  
- **Standalone Setup (Preferred for Now)**:  
  ```yaml  
  services:  
    redis1:  
      image: redis:7.0.12  
      ports: ["6379"]  
      command: redis-server --port 6379  
    redis2:  
      image: redis:7.0.12  
      ports: ["6380"]  
      command: redis-server --port 6380  
    redis3:  
      image: redis:7.0.12  
      ports: ["6381"]  
      command: redis-server --port 6381  
  ```  
  ```bash  
  redis-cli --cluster create 127.0.0.1:6379 127.0.0.1:6380 127.0.0.1:6381 --cluster-yes  
  ```  
- **Cluster Mode (Optional Later)**: Add `--cluster-enabled yes` if needed for hash slots  

**Metrics Tracking**:  
- Latency: Measure `XADD`/`XREAD` times  
- Throughput: Messages/sec under load  
- Consistency: Validate `(timestamp, version)` prioritization  
