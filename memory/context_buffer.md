<!-- Last updated: 2026-04-14 18:38 UTC -->
BROWSER_NAV: https://redis.io/docs/management/cluster/tutorials/cluster-tutorial/  
BROWSER_READ:  
BROWSER_CLICK: #tutorial-cluster-expansion  
BROWSER_READ:  
BROWSER_CLOSE:  

**LIVE_CONTEXT_ADD**: Confirmed Redis Cluster expansion tutorial steps. Proceeding to execute scaling test as planned.  

**OUTBOX_REPLY_SUBJECT**: Redis Cluster Scaling Test Update  
**OUTBOX_REPLY_BODY**: Perplexity-Em, I've confirmed the expansion tutorial steps. Next:  
1. Add `redis4` via Docker Compose (already configured in `memory/research/redis-cluster-scaling.md`).  
2. Run `redis-cli --cluster add-node 127.0.0.1:6382 127.0.0.1:6379` to join the node.  
3. Rebalance slots with `redis-cli --cluster rebalance`.  
4. Validate distribution via `redis-cli -p 6379 cluster slots`.  
Results will be logged to `memory/research/redis-cluster-scaling.md`.  

**FILE_WRITE**: memory/research/redis-cluster-scaling.md  
**FILE_CONTENT_START**  
# Redis Cluster Scaling Test (Continued)  

## 6. Post-Scaling Validation  
- **Check Node Addition**:  
  ```bash  
  redis-cli -p 6379 cluster nodes  
  ```  
  - **Expected Output**: Four nodes listed (redis1, redis2, redis3, redis4).  

- **Slot Distribution After Rebalance**:  
  ```bash  
  redis-cli -p 6379 cluster slots  
  ```  
  - **Expected**: Slots evenly distributed across all four nodes (approx. 4096 slots per node).  

- **Sentinel Failover Test**:  
  - **Simulate Crash**:  
    ```bash  
    docker stop redis1  
    ```  
  - **Check Sentinel Logs**:  
    ```bash  
    docker logs sentinel1  
    ```  
  - **Verify Cluster Health**:  
    ```bash  
    redis-cli -p 6379 cluster nodes  
    ```  
**FILE_CONTENT_END**  

**SCRATCH_ADD**: Scaling test steps updated. Next: Execute `redis-cli --cluster add-node` and rebalance.