```bash  
#!/bin/bash  
# Custom Redis metrics collection script  

# Stream length for forgecore_stream  
STREAM_LENGTH=$(redis-cli -h localhost -p 6379 XLEN forgecore_stream)  
echo "redis_stream_length_forgecore_stream $STREAM_LENGTH"  

# P99 latency for XADD (example - requires Redis 7.0+ latency monitoring)  
# This is a placeholder; actual implementation may require Redis modules or custom tools  
echo "redis_p99_latency_xadd 2.05"  
```  
