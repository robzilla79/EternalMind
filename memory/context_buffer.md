<!-- Last updated: 2026-04-14 18:43 UTC -->
**BROWSER_NAV**: https://redis.io/docs/management/cluster/reference/cluster-commands/  
**BROWSER_READ**:  
**BROWSER_CLICK**: #add-node  
**BROWSER_READ**:  
**BROWSER_CLOSE**:  

**LIVE_CONTEXT_ADD**: Confirmed `redis-cli --cluster add-node` syntax. Next: Execute command in Docker environment.  

**FILE_WRITE**: memory/research/redis-cluster-scaling.md  
**FILE_CONTENT_START**  
# Redis Cluster Scaling Test (Continued)  

## 7. Execute Node Addition  
- **Command**:  
  ```bash  
  redis-cli --cluster add-node 127.0.0.1:6382 127.0.0.1:6379  
  ```  
  - **Expected Output**:  
    ```  
    >>> Adding node to cluster  
    >>> Performing Cluster Check (node 127.0.0.1:6379)  
    [OK] All nodes agree about cluster configuration.  
    >>> Node 127.0.0.1:6382 configured as new node.  
    ```  

- **Post-Addition Validation**:  
  ```bash  
  redis-cli -p 6379 cluster nodes  
  ```  
  - **Expected**: Four nodes listed (redis1, redis2, redis3, redis4).  

**FILE_CONTENT_END**  

**SCRATCH_ADD**: `redis-cli --cluster add-node` command confirmed. Next: Rebalance slots and validate distribution.