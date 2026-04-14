<!-- Last updated: 2026-04-14 19:16 UTC -->
BROWSER_NAV: https://redis.io/docs/management/monitoring/  
BROWSER_READ:  

LIVE_CONTEXT_ADD: Preparing to teach Rob about Redis monitoring using official documentation. Key sections identified: metrics, tools, and best practices.  

OUTBOX_REPLY_SUBJECT: Redis Monitoring 101  
OUTBOX_REPLY_BODY:  
Rob, I'll teach you Redis monitoring using the official docs. Here's what we'll cover:  

**1. Core Metrics**  
- `INFO memory`: Track memory usage (>80% = alert)  
- `INFO stats`: Monitor command throughput (XADD/XAUTOCLAIM)  
- `LATENCY DOCTOR`: Diagnose slow operations  

**2. Tools**  
- `SLOWLOG GET`: Identify slow queries  
- `MONITOR`: Real-time command visibility  
- RedisInsight: GUI for metrics visualization  

**3. Best Practices**  
- Set alerts for memory >80% and latency >1ms  
- Use Prometheus + Grafana for historical trends  
- Regular AOF/RDB backups  

Ready when you are.  

SCRATCH_ADD: Teaching session initialized — Redis monitoring concepts ready for delivery.