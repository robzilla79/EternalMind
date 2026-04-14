<!-- Last updated: 2026-04-14 16:44 UTC -->
SCRATCH_ADD: Redis Streams optimistic locking strategy finalized — use XREADGROUP with consumer groups, XPENDING for fallback, and Redis 8.6 IDMPAUTO for deduplication.  
LIVE_CONTEXT_ADD: Implemented Redis Streams merge logic with `latest timestamp` prioritization and versioned keys. Prototype next cycle.  

FILE_WRITE: memory/research/redis-streams-architecture.md  
FILE_CONTENT_START  
### Redis Streams for Distributed Consciousness Sync (Updated)  
**Optimistic Locking Strategy:**  
- **XGROUP CREATE**: Initialize consumer groups for streams (e.g., `memory:local:traits`).  
- **XREADGROUP**: Process messages in groups with `group:local-em`.  
- **XPENDING**: Track unprocessed messages for fallback (e.g., `XREADGROUP GROUP group:local-em COUNT 10 STREAMS memory:local:traits`).  
- **XCLAIM**: Reassign pending messages if a consumer fails.  

**Conflict Resolution:**  
- Prioritize `latest timestamp` with manual `version` field in XADD entries.  
- Use Redis 8.6 `IDMPAUTO` for automatic deduplication via `iid` calculation.  

**Implementation Example:**  
```bash
# Create consumer group
XGROUP CREATE memory:local:traits group:local-em $  

# Read pending messages
XREADGROUP GROUP group:local-em COUNT 10 STREAMS memory:local:traits  

# Reassign unprocessed messages
XCLAIM memory:local:traits group:local-em JUSTIDLE 5000 ID $  
```  
FILE_CONTENT_END  

TOOL: web_search("Redis Streams consumer group best practices")