# RedisInsight Setup for Real-Time Monitoring

**Steps to configure RedisInsight for 24h monitoring:**

1. **Install RedisInsight** via Docker:
```bash
docker run -d -p 8081:8081 redis/redisinsight:latest
```

2. **Connect to Redis 8.6 instance**:
   - Open RedisInsight in browser: http://localhost:8081
   - Add Redis connection: 
     - Host: redis-host
     - Port: 6379
     - Authentication: redis-password

3. **Set up stream monitoring**:
   - Navigate to "Streams" tab
   - Select your phi_stream
   - Enable "Auto-refresh" at 10s interval
   - Configure alerts for:
     - Pending messages > 20% of stream size
     - XPENDING IDLE > 60s
     - MAX_IID > 1000

4. **Export metrics**:
   - Use "Export" > "CSV" for historical data analysis
   - Enable "Real-time metrics" in the dashboard

**Note:** Ensure RedisInsight is running in the same network as your Redis instance. Use `docker network inspect` to verify connectivity.
