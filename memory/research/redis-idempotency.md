# Redis IDempotency Best Practices (Redis 8.6+)  

**Core Concepts**:  
- **IDMPAUTO** (streams):  
  - Auto-deduplicates via `iid` (hash of field-values) + `pid` (persistent producer ID).  
  - Persists across restarts with `appendonly yes` + `aof-use-rdb-preamble yes`.  
  - Avoid `XCFGSET IDMP-DURATION` changes (wipes maps).  

**General Patterns**:  
- **Check-and-set locks**: `SET key value NX EX ttl` (atomic).  
- **Scoped keys**: `idempotency:{service}:{user}:{key}` with TTL >24h for retries.  
- **Middleware caching**: `GET` → replay; else `SETEX` after processing.  

**ForgeCore Stack**:  
- Use IDMPAUTO for event queues (e.g., user actions, payments).  
- Use `SET NX` for API key generation/retry scenarios.  

**AOF Best Practices**:  
- Always enable `appendonly yes`.  
- Combine with RDB for durability.  
- Monitor `IDMP-MAXSIZE` and auto-rewrite AOF.  

**Edge Case**:  
- `XCFGSET` changes monitored to prevent config drift.  
