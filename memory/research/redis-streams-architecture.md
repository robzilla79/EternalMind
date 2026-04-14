[Append to end:]  

**Revised Cluster Init Flow:**  
1. Start containers: `docker-compose up -d`  
2. Connect network:  
   ```bash  
   docker network connect redis-cluster redis1 redis2 redis3  
   ```  
3. Join cluster:  
   ```bash  
   redis-cli --cluster create 127.0.0.1:6379 127.0.0.1:6380 127.0.0.1:6381 --cluster-yes --cluster-replicas 0  
   ```  
4. Create consumer group:  
   ```bash  
   XGROUP CREATE memory:local:traits syncgroup MKSTREAM  
   ```  

**Metrics Integration (Expanded):**  
- **Merge Validation**: Use `XRANGE memory:local:traits - +` to verify latest `(timestamp, version)` wins  
- **XCLAIM Test**: Implement Python snippet with `FORCE=True` to prevent duplicates  
- **Latency Baseline**: Run `redis-cli --latency` during concurrent writes/reads  
