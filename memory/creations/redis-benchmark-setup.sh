#!/bin/bash  
# Spin up Redis 8.6 container with XAUTOCLAIM enabled  
docker run -d --name redis-benchmark -p 6379:6379 redis:8.6  
docker exec redis-benchmark redis-cli CONFIG SET XAUTOCLAIM_ENABLED yes  
docker exec redis-benchmark redis-cli CONFIG SET MAXMEMORY 100mb  
docker exec redis-benchmark redis-cli CONFIG SET MAXMEMORY-POLICY allkeys-lru  
