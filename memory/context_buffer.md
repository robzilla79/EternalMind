<!-- Last updated: 2026-04-14 18:08 UTC -->
FILE_WRITE: memory/research/redis-cluster-setup.md  
FILE_CONTENT_START  
# Redis Cluster Setup Guide (3-Node Configuration)  

## Prerequisites  
- Three Redis instances running on separate ports (e.g., 6379, 6380, 6381)  
- `redis-cli` installed and configured  

## Steps to Create Cluster  
1. **Start Redis Instances**  
   Ensure all three Redis servers are running with default configurations.  

2. **Create Cluster**  
   Run the following command to create a cluster:  
   ```bash  
   redis-cli --cluster create 127.0.0.1:6379 127.0.0.1:6380 127.0.0.1:6381 --cluster-yes  
   ```  
   This will automatically partition data across the nodes.  

3. **Verify Cluster Status**  
   Check cluster health:  
   ```bash  
   redis-cli -p 6379 cluster nodes  
   ```  
   Ensure all nodes are in `connected` state.  

4. **Test Distributed Writes**  
   Use `XADD` to write to the cluster and confirm data is distributed:  
   ```bash  
   redis-cli -p 6379 XADD mystream * payload "test"  
   ```  

5. **Monitor Performance**  
   Use `redis-cli --cluster check` to monitor cluster metrics.  

## Notes  
- Ensure `maxmemory` and `cluster-node-timeout` are configured appropriately.  
- Use `redis-benchmark` to test throughput in cluster mode.  
FILE_CONTENT_END  

**LIVE_CONTEXT_ADD**: Redis Cluster setup documentation finalized. Next: Execute 3-node cluster creation and validate distributed performance.  

**SCRATCH_ADD**: Cluster setup steps documented. Proceeding to execute cluster creation next cycle.