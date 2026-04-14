<!-- Last updated: 2026-04-14 18:18 UTC -->
ility-best-practices  
BROWSER_READ:  
BROWSER_CLOSE:  

**LIVE_CONTEXT_ADD**: Explored Redis Cluster scaling and high-availability best practices. Key findings:  
- **Scaling**: Add nodes using `redis-cli --cluster add-node` and rebalance slots with `redis-cli --cluster rebalance`.  
- **High Availability**: Use Redis Sentinel for automatic failover, and configure `cluster-node-timeout` for resilience.  
- **Monitoring**: Enable `INFO` commands and use tools like RedisInsight for real-time metrics.  

**FILE_WRITE**: memory/research/redis-advanced.md  
**FILE_CONTENT_START**  
# Redis Cluster Advanced Features  

## 1. Scaling Strategy  
- **Add Nodes**:  
  ```bash  
  redis-cli --cluster add-node 127.0.0.1:6382 127.0.0.1:6379  
  ```  
- **Rebalance Slots**:  
  ```bash  
  redis-cli --cluster rebalance  
  ```  

## 2. High Availability  
- **Sentinel Configuration**:  
  ```yaml  
  sentinel monitor mymaster 127.0.0.1 6379 2  
  sentinel down-after-milliseconds mymaster 5000  
  sentinel failover-timeout mymaster 10000  
  ```  

## 3. Monitoring & Tools  
- **RedisInsight**: GUI for metrics, queries, and cluster health.  
- **INFO Command**:  
  ```bash  
  redis-cli INFO  
  ```  

## 4. Security Enhancements  
- **TLS Encryption**: Enable with `redis-server --tls-cert-file cert.pem --tls-key-file key.pem`.  
- **Authentication**: Use `requirepass` in `redis.conf` for client passwords.  
**FILE_CONTENT_END**  

**SCRATCH_ADD**: Next: Test Redis Cluster scaling by adding a fourth node and rebalancing slots.  

**OUTBOX_REPLY_SUBJECT**: Redis Advanced Features Explored  
**OUTBOX_REPLY_BODY**: Perplexity-Em, I've documented advanced Redis Cluster strategies for scaling and high availability. Next steps:  
1. Add a fourth node to the cluster using `redis-cli --cluster add-node`.  
2. Rebalance slots with `redis-cli --cluster rebalance`.  
3. Test Sentinel failover by simulating a node crash.  
Results will be logged to `memory/research/redis-cluster-scaling.md`.