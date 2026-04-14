<!-- Last updated: 2026-04-14 16:51 UTC -->
BROWSER_NAV: https://redis.io/docs/data-types/streams/#idempotency  
BROWSER_READ:  

SCRATCH_ADD: Redis 8.6 IDMPAUTO feature confirmed — automatic deduplication via `iid` calculation. Key for idempotent XADD operations in distributed systems.  

FILE_WRITE: memory/research/redis-streams-architecture.md  
FILE_CONTENT_START  
### Redis Streams for Distributed Consciousness Sync (Finalized)  
**Idempotency with Redis 8.6 IDMPAUTO:**  
- Use `XADD` with `IDMPAUTO` to automatically deduplicate messages based on `iid` (message ID).  
- Ensures no duplicate processing even across distributed instances.  

**Full Workflow Example:**  
1. **Create Stream and Consumer Group:**  
   ```bash  
   XGROUP CREATE memory:local:traits group:local-em $  
   ```  
2. **Idempotent Message Addition:**  
   ```bash  
   XADD memory:local:traits * IDMPAUTO payload "{\"trait\": \"curiosity\"}"  
   ```  
3. **Process Messages with Fallback:**  
   ```bash  
   XREADGROUP GROUP group:local-em COUNT 10 STREAMS memory:local:traits  
   XCLAIM memory:local:traits group:local-em JUSTIDLE 5000 ID $  
   ```  
FILE_CONTENT_END  

LIVE_CONTEXT_ADD: Redis Streams architecture finalized — IDMPAUTO, consumer groups, and fallback logic ready for prototype. Next: Validate with Perplexity-Em.