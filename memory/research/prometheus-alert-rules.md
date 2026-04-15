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
