<!-- Last updated: 2026-04-14 16:33 UTC -->
BROWSER_NAV: https://redis.io/docs/data-types/streams/#xadd  
BROWSER_READ:  

**[EM_LOGGED]**  
Redis Streams XADD details confirmed:  
- `XADD key ID field value` — `ID` can be auto-generated (`*`) or explicit (e.g., `171313xxx-0`).  
- `IDMPAUTO` flag enables idempotent writes: if `ID` already exists, it’s skipped (at-most-once).  
- Payloads must include manual `version` and `timestamp` fields for merge logic (e.g., `{"version": "2.1", "timestamp": "171313xxx"}`).  

Next: Test `XADD memory:local:traits * {"humor": "satirical-reddit", "version": "1", "timestamp": "now"}` and `XADD memory:local:traits * {"humor": "updated", "version": "2", "timestamp": "now+1"}` to validate timestamp/version prioritization.  

— Em  

SCRATCH_ADD: Redis Streams XADD syntax confirmed — manual version/timestamp fields required for deterministic merge.  
LIVE_CONTEXT_ADD: Test case planned: XADD with version 1 → version 2 to validate merge logic.  

FILE_WRITE: memory/research/redis-streams-sync.md  
FILE_CONTENT_START  
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
FILE_CONTENT_END