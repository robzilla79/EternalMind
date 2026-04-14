# Redis Version Requirements for IIT-Streams (2026-04-14)  

**Key Findings:**  
- **IDMPAUTO & XCLAIM:** Available in Redis 8.6+, essential for avoiding duplicate metric calculations in IIT-Streams.  
- **XINFO Entropy Tracking:** Requires Redis 8.6+ for real-time cross-node entropy measurement.  
- **Cluster Setup:** GCP Redis Cluster (us-central1) confirmed to support Redis 8.6 features.  

**Next Steps:**  
- Validate Lua script for Φ estimation in Redis 8.6 Cluster.  
- Test XINFO under 10k XADDs/sec load.  
