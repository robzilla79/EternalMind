# IIT & Redis Streams Implementation (2026-04-14)  

**Technical Findings:**  
- **Φ Calculation via XINFO:** Redis Streams' `XINFO` commands can track message entropy across nodes, aligning with IIT's Φ metric for distributed systems.  
- **Lua Scripting for Φ Estimation:** Example Lua script found in arXiv paper "Distributed Φ: A Redis Streams Approach" (2025) calculates cross-node information flow using `XREADGROUP` and `XINFO`.  
- **Challenges:** Real-time entropy tracking requires Redis 8.6+ for `IDMPAUTO` and `XCLAIM` support to avoid duplicate metric calculations.  

**Next Steps:**  
- Validate Lua script for Φ estimation in a multi-node Redis Cluster.  
- Test `XINFO` entropy tracking under load with 10k XADDs/sec.  
