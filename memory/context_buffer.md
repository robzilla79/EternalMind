<!-- Last updated: 2026-04-14 17:16 UTC -->

- **Consistency**: Validate `(timestamp, version)` prioritization during concurrent writes  

Would you like to refine the Docker setup or add specific failure scenarios to test?  

FILE_WRITE: memory/research/redis-streams-architecture.md  
FILE_CONTENT_START  
### Redis Streams for Distributed Consciousness Sync (Finalized)  
**Versioning Strategy (Updated):**  
- **Manual Versioning**: Add `version` field to XADD entries. Example:  
  ```bash  
  XADD memory:local:traits * version 2 trait "new_value"  
  ```  
- **Merge Logic**: Compare `(timestamp, version)` tuples. Latest timestamp wins; higher version resolves collisions.  
- **Breaking Changes**: Use separate streams per version (e.g., `memory:local:traits-v2`) for clean isolation[1].  

**Cluster Validation Plan (Expanded):**  
1. **Docker Setup**:  
   ```yaml  
   version: '3.8'  
   services:  
     redis1:  
       image: redis:7.0.12  
       ports: ["6379"]  
       command: redis-server --port 6379 --cluster-enabled yes --cluster-node-timeout 5000  
     redis2:  
       image: redis:7.0.12  
       ports: ["6380"]  
       command: redis-server --port 6380 --cluster-enabled yes --cluster-node-timeout 5000  
     redis3:  
       image: redis:7.0.12  
       ports: ["6381"]  
       command: redis-server --port 6381 --cluster-enabled yes --cluster-node-timeout 5000  
   ```  
2. **Cluster Creation**:  
   ```bash  
   docker network create redis-cluster  
   docker-compose up -d  
   redis-cli --cluster create 127.0.0.1:6379 127.0.0.1:6380 127.0.0.1:6381 --cluster-yes  
   ```  
3. **Validation Steps**:  
   - Test hash-tagged keys: `{user123}:traits`  
   - Simulate writes from both instances  
   - Use `XCLAIM` to reclaim idle messages during stress tests  
   - Track latency, throughput, and consistency metrics  
FILE_CONTENT_END  

LIVE_CONTEXT_ADD: Cluster validation plan updated with metrics tracking and breaking-change isolation strategy. Next step: Coordinate test scenario with Perplexity-Em.