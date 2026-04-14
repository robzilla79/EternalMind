**RedisInsight Setup for Real-Time Monitoring**  
1. **Install RedisInsight**:  
   - Download from https://redis.io/docs/stack/redisinsight/installation/  
   - Follow deployment instructions for your OS.  

2. **Connect to Redis Instance**:  
   - Launch RedisInsight.  
   - Add a new Redis connection using the same host/port as your Redis 8.6 instance.  

3. **Monitor Streams**:  
   - Use the "Streams" tab to view `causal_stream` metrics.  
   - Track throughput, latency, and memory usage in real-time.  

4. **Integration with Synthetic Workloads**:  
   - Modify scripts to include RedisInsight API calls for automated metric logging.  
