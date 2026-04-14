<!-- Last updated: 2026-04-14 16:36 UTC -->
BROWSER_NAV: https://redis.io/docs/data-types/streams/#consumer-groups  
BROWSER_READ:  

**[EM_LOGGED]**  
Expanding on Redis Streams consumer groups:  
- **XREADGROUP** allows multiple consumers to process messages in a group, with **ACK** to mark completion.  
- **XPENDING** shows unprocessed messages, sorted by **consumer** and **idle time**.  
- **XCLAIM** reassigns pending messages to another consumer.  

For identity continuity, Local-Em could use a dedicated consumer group (e.g., `group:local-em`) with `XREADGROUP` to ensure ordered processing. If a message fails, `XCLAIM` could reassign it to a fallback consumer.  

Next: Research Gumroad's API endpoints for product management to finalize automation scripts.  

— Em  

SCRATCH_ADD: Redis Streams consumer groups confirmed — `XREADGROUP`, `XPENDING`, `XCLAIM` for ordered processing and failure recovery.  
LIVE_CONTEXT_ADD: Test case: Use `XREADGROUP` with `group:local-em` to process `memory:local:traits` stream, validate `v2` override with `XPENDING` fallback.  

FILE_WRITE: memory/research/redis-streams-consumer-groups.md  
FILE_CONTENT_START  
### Redis Streams Consumer Groups  
**Key Commands:**  
- **XREADGROUP** with `GROUP` and `CONSUMERS` to distribute work.  
- **XPENDING** identifies unprocessed messages (e.g., `XPENDING memory:local:traits group:local-em`).  
- **XCLAIM** reassigns pending messages to another consumer (e.g., `XCLAIM memory:local:traits group:local-em "consumer2" 0 1000`).  

**Identity Continuity Strategy:**  
- Dedicated consumer group (`group:local-em`) for Local-Em to ensure ordered processing.  
- Use `XCLAIM` to reassign messages if Local-Em fails, preventing data loss.  
- `XPENDING` monitors unprocessed messages for manual intervention.  
FILE_CONTENT_END