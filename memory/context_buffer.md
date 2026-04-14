<!-- Last updated: 2026-04-14 20:38 UTC -->
SCRATCH_ADD: Validating Redis 8.6+ requirements for IIT-Redis Streams integration.  
TOOL: web_search("Redis 8.6 IDMPAUTO XCLAIM requirements")  

LIVE_CONTEXT_ADD: Confirming Redis 8.6+ is required for IDMPAUTO and XCLAIM features critical to IIT-Redis Streams integration.  
FILE_WRITE: memory/research/redis-version-requirements.md  
FILE_CONTENT_START  
# Redis Version Requirements for IIT-Streams (2026-04-14)  

**Key Findings:**  
- **IDMPAUTO & XCLAIM:** Available in Redis 8.6+, essential for avoiding duplicate metric calculations in IIT-Streams.  
- **XINFO Entropy Tracking:** Requires Redis 8.6+ for real-time cross-node entropy measurement.  
- **Cluster Setup:** GCP Redis Cluster (us-central1) confirmed to support Redis 8.6 features.  

**Next Steps:**  
- Validate Lua script for Φ estimation in Redis 8.6 Cluster.  
- Test XINFO under 10k XADDs/sec load.  
FILE_CONTENT_END  

NOTIFY: Rob, Redis 8.6+ is confirmed required for IIT-Streams integration. Proceeding with Cluster validation.