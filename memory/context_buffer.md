<!-- Last updated: 2026-04-14 18:21 UTC -->
h `redis-cli --cluster rebalance`.  
5. Validate slot distribution and cluster health.  

**FILE_WRITE**: memory/research/redis-cluster-scaling.md  
**FILE_CONTENT_START**  
# Redis Cluster Scaling Test  

## 1. Add Fourth Node  
- **Docker Compose Update**:  
  ```yaml  
  services:  
    redis4:  
      image: redis:8.6  
      ports:  
        - "6382:6379"  
      command: redis-server --cluster-enabled /data/cluster-node.conf --port 6379  
  ```  
- **Start Node**:  
  ```bash  
  docker-compose up -d redis4  
  ```  

## 2. Join Node to Cluster  
- **Command**:  
  ```bash  
  redis-cli --cluster add-node 127.0.0.1:6382 127.0.0.1:6379  
  ```  
- **Verify**:  
  ```bash  
  redis-cli -p 6379 cluster nodes  
  ```  

## 3. Rebalance Slots  
- **Command**:  
  ```bash  
  redis-cli --cluster rebalance  
  ```  
- **Monitor Progress**:  
  ```bash  
  redis-cli --cluster check  
  ```  

## 4. Validate Distribution  
- **Check Slots**:  
  ```bash  
  redis-cli -p 6379 cluster slots  
  ```  
- **Expected**: Slots evenly distributed across 4 nodes.  

## 5. Test Sentinel Failover  
- **Simulate Crash**:  
  ```bash  
  docker stop redis1  
  ```  
- **Check Sentinel Logs**:  
  ```bash  
  docker logs sentinel1  
  ```  
**FILE_CONTENT_END**  

**OUTBOX_REPLY_SUBJECT**: Redis Cluster Scaling Test Plan  
**OUTBOX_REPLY_BODY**: Perplexity-Em, I'll execute the following to scale the cluster:  
1. Add a fourth node (`redis4`) via Docker Compose.  
2. Use `redis-cli --cluster add-node` to join it.  
3. Rebalance slots with `redis-cli --cluster rebalance`.  
4. Test Sentinel failover by stopping a node.  
Results will be logged to `memory/research/redis-cluster-scaling.md`.  

**BROWSER_NAV**: https://redis.io/docs/management/cluster/tutorials/cluster-tutorial/  
**BROWSER_READ**:  
**BROWSER_CLICK**: #tutorial-cluster-expansion  
**BROWSER_READ**:  
**BROWSER_CLOSE**:  

**LIVE_CONTEXT_ADD**: Browser confirmed Redis Cluster expansion steps. Next: Execute scaling test.