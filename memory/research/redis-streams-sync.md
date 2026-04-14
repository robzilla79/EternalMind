### Redis Streams for Distributed Sync  
**Key Commands:**  
- **XADD** with `IDMPAUTO` for deduplication.  
- **XPENDING** to resolve conflicts via timestamp + version.  
- **XREADGROUP** for ordered processing with consumer groups.  

**Merge Logic:**  
1. Use manual `version` and `timestamp` in payloads (e.g., `{"version": "2.1", "timestamp": "171313xxx"}`).  
2. Prioritize **latest timestamp** + **highest version** during merges (e.g., `XRANGE` sorted by `ts-desc`, then `version-asc`).  
3. Trim streams with `MAXLEN~` to prevent unbounded growth.  

**Test Case:**  
- Send `XADD memory:local:traits * {"humor": "v1", "version": "1", "timestamp": "now"}`.  
- Send `XADD memory:local:traits * {"humor": "v2", "version": "2", "timestamp": "now+1"}`.  
- Validate that `v2` overrides `v1` due to higher version + timestamp.  
