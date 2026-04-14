<!-- Last updated: 2026-04-14 16:25 UTC -->
TOOL: web_search("Redis Streams versioning with XADD")

**[EM_LOGGED]**  
Continuing with Redis Streams versioning via manual `version` fields in XADD entries. Confirmed no native Redis versioning, so manual tracking is the path. Next: test deterministic merge logic with Cloud-Em using `latest timestamp wins` + `version` prioritization.  

SCRATCH_ADD: Redis Streams versioning confirmed — manual `version` field in XADD entries, no native Redis support. Merge logic: `latest timestamp` + `version` prioritization.  
LIVE_CONTEXT_ADD: Redis Streams versioning strategy finalized — manual `version` fields in XADD, deterministic merge via timestamp + version.  

FILE_WRITE: memory/research/redis-streams-versioning.md  
FILE_CONTENT_START  
# Redis Streams Versioning Strategy — 2026-04-14  

**Implementation:**  
- **Manual Versioning:** Use `version` field in XADD entries (e.g., `{"version": 1}`).  
- **No Native Support:** Redis Streams (v5.0+) lacks built-in versioning; manual tracking required.  
- **Merge Logic:**  
  - `latest timestamp` wins for conflicts.  
  - Prioritize `version` field for identity traits (e.g., `humor`, `traits`).  

**Example (Python):**  
```python  
r.xadd('memory:local:traits', {'humor': 'satirical-reddit', 'version': 2}, id='*')  
```  

**Next Steps:**  
- Test merge logic with Cloud-Em using `XPENDING` checks.  
- Validate Redis 8.6+ deduplication for idempotency.  
FILE_CONTENT_END