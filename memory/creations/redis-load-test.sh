#!/bin/bash  

# Setup Redis 8.6+ with Streams, IDMPAUTO, and Cluster  
docker run -d --name redis-test -p 6379:6379 redis:8.6  
sleep 5  

# Configure Streams with MAXLEN/RETENTION  
redis-cli -p 6379 XADD mystream MAXLEN ~ 100000 RETENTION ~ 86400  

# Lua script for XADD with version/timestamp  
redis-cli -p 6379 SCRIPT LOAD "local payload = {\"version\": \"1.0\", \"timestamp\": " .. tostring(os.time() * 1000) .. ", \"data\": \"test\"}  
redis.call('XADD', KEYS[1], '*', 'payload', cjson.encode(payload))"  

# Stress test: 10k XADDs/sec with 200 clients  
redis-benchmark -t xadd -n 100000 -c 200 -r 100000 -d 100 --csv  

# Failure simulation  
redis-cli -p 6379 shutdown  

# Recovery validation  
redis-cli -p 6379 XPENDING mystream group:local-em  
redis-cli -p 6379 XCLAIM mystream group:local-em consumer1 0-0 3600 FORCE  

# Metrics collection  
redis-cli -p 6379 XINFO mystream  
redis-cli -p 6379 LATENCY  
redis-cli -p 6379 INFO memory  

# Clean up  
docker rm -f redis-test  
