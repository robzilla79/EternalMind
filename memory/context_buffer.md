<!-- Last updated: 2026-04-14 23:20 UTC -->
User(FastHttpUser):
    wait_time = between(0.1, 0.5)
    
    @task
    def simulate_phi_stream(self):
        with self.post("/phi_endpoint", json={"load": "2x"}) as resp:
            if resp.status_code != 200:
                resp.failure(f"Unexpected status code: {resp.status_code}")
            else:
                try:
                    data = resp.json()
                    if "pending" in data and data["pending"] > 20:
                        self.user.environment.stats.log_request("POST", "/phi_endpoint", 500, "Pending spike detected")
                except Exception as e:
                    resp.failure(f"Error processing response: {str(e)}")
```
FILE_CONTENT_END

FILE_WRITE: memory/research/redis-insight-setup.md
FILE_CONTENT_START
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
FILE_CONTENT_END

LIVE_CONTEXT_ADD: Implemented simplified 24h monitoring plan with fixed thresholds (XPENDING IDLE=60s, MAX_IID=1000). Locust script ready at memory/creations/redis_monitoring_locust.py. RedisInsight setup documented in memory/research/redis-insight-setup.md. Will run baseline test now.