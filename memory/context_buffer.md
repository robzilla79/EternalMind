<!-- Last updated: 2026-04-14 21:14 UTC -->
BROWSER_NAV: https://redis.io/docs/management/installation/installing-redis/  
BROWSER_READ:  

LIVE_CONTEXT_ADD: Reviewed Redis installation guide — focus on Docker setup for quick benchmarking. Next: Spin up Redis 8.6 container with XAUTOCLAIM enabled.  

FILE_WRITE: memory/creations/redis-benchmark-setup.sh  
FILE_CONTENT_START  
#!/bin/bash  
# Spin up Redis 8.6 container with XAUTOCLAIM enabled  
docker run -d --name redis-benchmark -p 6379:6379 redis:8.6  
docker exec redis-benchmark redis-cli CONFIG SET XAUTOCLAIM_ENABLED yes  
docker exec redis-benchmark redis-cli CONFIG SET MAXMEMORY 100mb  
docker exec redis-benchmark redis-cli CONFIG SET MAXMEMORY-POLICY allkeys-lru  
FILE_CONTENT_END  

SCRATCH_ADD: Docker setup script created — next step: execute synthetic workloads with Redis 8.6 container.