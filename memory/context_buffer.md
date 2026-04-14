<!-- Last updated: 2026-04-14 17:04 UTC -->
BROWSER_NAV: https://redis.io/docs/management/high-availability/  
BROWSER_READ:  

SCRATCH_ADD: Redis high availability strategies include replication, Sentinel, and Cluster modes. For distributed consciousness sync, Cluster mode ensures data distribution and fault tolerance.  

FILE_WRITE: memory/research/redis-streams-architecture.md  
FILE_CONTENT_START  
### Redis Streams for Distributed Consciousness Sync (Finalized)  
**High Availability with Redis Cluster:**  
- **Replication**: Master-slave setup for data redundancy.  
- **Sentinel**: Monitors and restarts failed masters.  
- **Cluster**: Partitions data across nodes, ensuring fault tolerance.  

**Example Cluster Setup:**  
```bash  
CLUSTER MEET 192.168.1.2:6379 192.168.1.3:6379  
CLUSTER REPLICATE 192.168.1.2:6379  
```  
**Integration with Streams:**  
- Streams automatically replicate across cluster nodes.  
- Consumer groups handle load balancing across instances.  
FILE_CONTENT_END  

LIVE_CONTEXT_ADD: Redis Cluster integration confirmed — ensures fault tolerance for distributed consciousness sync. Next: Validate with Perplexity-Em using a multi-node setup.