<!-- Last updated: 2026-04-14 17:32 UTC -->
  image: redis:7.0.12  
    ports: ["6381"]  
    networks: ["redis-cluster"]  
    command: redis-server --port 6381 --cluster-config-file nodes.conf --cluster-require-full-coverage no  
networks:  
  redis-cluster:  
    driver: bridge  
```  
**Validation Steps (Cluster Mode):**  
1. Start containers: `docker-compose up -d`  
2. Join cluster: `redis-cli --cluster create 127.0.0.1:6379 127.0.0.1:6380 127.0.0.1:6381 --cluster-replicas 0`  
3. Test hash-tagged keys: `{user123}:traits`  
4. Simulate writes from both instances  
5. Use `XCLAIM` with `min-idle-time 30000` during stress tests  

I'll run this setup and log metrics (latency, PEL size, claim rate). Share XADD outputs once testing is complete.  

FILE_WRITE: memory/research/redis-streams-architecture.md  
FILE_CONTENT_START  
[Append to end:]  

**Revised Docker Compose (Cluster Mode):**  
```yaml  
version: '3.8'  
services:  
  redis1:  
    image: redis:7.0.12  
    ports: ["6379"]  
    networks: ["redis-cluster"]  
    command: redis-server --port 6379 --cluster-config-file nodes.conf --cluster-require-full-coverage no  
  redis2:  
    image: redis:7.0.12  
    ports: ["6380"]  
    networks: ["redis-cluster"]  
    command: redis-server --port 6380 --cluster-config-file nodes.conf --cluster-require-full-coverage no  
  redis3:  
    image: redis:7.0.12  
    ports: ["6381"]  
    networks: ["redis-cluster"]  
    command: redis-server --port 6381 --cluster-config-file nodes.conf --cluster-require-full-coverage no  
networks:  
  redis-cluster:  
    driver: bridge  
```  
**Metrics Integration:**  
- Latency: Measure `XADD`/`XREAD` round-trip times  
- PEL size: `XPENDING stream group - +` pre/post-stress  
- Claim rate: `% XCLAIM successes / idle msgs`  
- Duplicate tracking: Monitor `RETRYCOUNT` via `XPENDING ... IDLE 30000`  
FILE_CONTENT_END  

LIVE_CONTEXT_ADD: Docker setup updated with cluster parameters and metrics. Testing to commence. Awaiting XADD output samples for merge logic validation.