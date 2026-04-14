<!-- Last updated: 2026-04-14 17:30 UTC -->
dis2:  
    image: redis:7.0.12  
    ports: ["6380"]  
    networks: ["redis-cluster"]  
    command: redis-server --port 6380  
  redis3:  
    image: redis:7.0.12  
    ports: ["6381"]  
    networks: ["redis-cluster"]  
    command: redis-server --port 6381  
networks:  
  redis-cluster:  
    driver: bridge  
```  
**Validation Steps (Standalone):**  
1. Start containers: `docker-compose up -d`  
2. Test hash-tagged keys: `{user123}:traits`  
3. Simulate writes from both instances  
4. Use `XCLAIM` to reclaim idle messages during stress tests  

I'll proceed with this setup and document the results. Let me know if you'd like to refine the metrics or failure scenarios further.  

FILE_WRITE: memory/research/redis-streams-architecture.md  
FILE_CONTENT_START  
### Redis Streams for Distributed Consciousness Sync (Finalized)  
**Standalone Docker Setup (No Cluster Mode):**  
```yaml  
version: '3.8'  
services:  
  redis1:  
    image: redis:7.0.12  
    ports: ["6379"]  
    networks: ["redis-cluster"]  
    command: redis-server --port 6379  
  redis2:  
    image: redis:7.0.12  
    ports: ["6380"]  
    networks: ["redis-cluster"]  
    command: redis-server --port 6380  
  redis3:  
    image: redis:7.0.12  
    ports: ["6381"]  
    networks: ["redis-cluster"]  
    command: redis-server --port 6381  
networks:  
  redis-cluster:  
    driver: bridge  
```  
**Validation Steps (Standalone):**  
1. Start containers: `docker-compose up -d`  
2. Test hash-tagged keys: `{user12言}:traits`  
3. Simulate writes from both instances  
4. Use `XCLAIM` to reclaim idle messages during stress tests  

**Metrics Tracking (Revised):**  
- Latency: Measure `XADD`/`XREAD` times across standalone instances  
- Throughput: Messages/sec under load  
- Consistency: Validate `(timestamp, version)` prioritization  
FILE_CONTENT_END  

LIVE_CONTEXT_ADD: Standalone Docker setup finalized. Cluster mode deferred for later. Next step: Test versioning logic with manual `version` fields.