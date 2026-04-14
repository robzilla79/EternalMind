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
