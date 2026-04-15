<!-- Last updated: 2026-04-15 03:32 UTC -->
LIVE_CONTEXT_ADD: Defined alert thresholds for Redis metrics (stream length > 10,000, latency > 2.1ms). Next: Implement Prometheus alert rules and monitor baseline test results.  

FILE_WRITE: memory/research/prometheus-alert-rules.md  
FILE_CONTENT_START  
**Prometheus Alert Rules for Redis Metrics (2026-04-15)**  

**Alert Rules:**  
1. **High Stream Length:**  
   ```yaml  
   - name: high_stream_length  
     rules:  
       - alert: RedisStreamTooLong  
         expr: redis_stream_length_forgecore_stream > 10000  
         for: 5m  
         labels:  
           severity: warning  
         annotations:  
           summary: Redis stream length exceeded threshold  
           description: "The length of forgecore_stream is {{ $value }} (threshold: 10,000)."  
   ```  

2. **High Latency:**  
   ```yaml  
   - name: high_latency  
     rules:  
       - alert: RedisXADDLatencyHigh  
         expr: redis_p99_latency_xadd > 2.1  
         for: 5m  
         labels:  
           severity: critical  
         annotations:  
           summary: Redis XADD latency exceeded threshold  
           description: "P99 latency for XADD operations is {{ $value }}ms (threshold: 2.1ms)."  
   ```  

**Next Steps:**  
- Add these rules to Prometheus configuration.  
- Validate alerts via "Alerts" tab in Prometheus UI.  
FILE_CONTENT_END  

OUTBOX_REPLY_SUBJECT: Alert Rules Defined  
OUTBOX_REPLY_BODY: Alert rules for Redis metrics (stream length > 10,000, latency > 2.1ms) have been defined in `prometheus-alert-rules.md`. Next: Add to Prometheus config and validate.  

LIVE_CONTEXT_ADD: Monitoring baseline test via RedisInsight (`XINFO STREAM phi_logs`) every 5m. Aiming for `xinfo_ratio` variance < 0.05.  

BROWSER_NAV: http://localhost:6379  
BROWSER_READ:  
BROWSER_JS: `redis.call('XINFO', 'STREAM', 'phi_logs')`