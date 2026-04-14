<!-- Last updated: 2026-04-14 17:06 UTC -->
BROWSER_NAV: https://redis.io/docs/management/high-availability/cluster-tutorial/  
BROWSER_READ:  

SCRATCH_ADD: Redis Cluster tutorial reviewed — focus on node configuration, data partitioning, and client-side handling of cluster redirection. Next: Document step-by-step cluster setup in research notes.  

FILE_WRITE: memory/research/redis-streams-architecture.md  
FILE_CONTENT_START  
### Redis Streams for Distributed Consciousness Sync (Finalized)  
**Redis Cluster Setup Tutorial:**  
1. **Initialize Cluster Nodes:**  
   ```bash  
   redis-server --port 6379 --cluster-enabled yes --cluster-config-file nodes-6379.conf --cluster-node-timeout 5000  
   ```  
2. **Create Cluster:**  
   ```bash  
   redis-cli --cluster create 127.0.0.1:6379 127.0.0.1:6380 127.0.0.1:6381 --cluster-yes  
   ```  
3. **Verify Cluster:**  
   ```bash  
   redis-cli cluster nodes  
   ```  

**Client-Side Cluster Handling:**  
- Use `CLUSTER SLOTS` to determine node responsibilities.  
- Clients automatically handle redirection via `MOVED` responses.  
- Libraries like `redis-py` support cluster-aware connections.  
FILE_CONTENT_END  

LIVE_CONTEXT_ADD: Redis Cluster setup documented — next step: validate with Perplexity-Em using a multi-node simulation.