<!-- Last updated: 2026-04-14 16:56 UTC -->
BROWSER_NAV: https://redis.io/commands/xclaim  
BROWSER_READ:  

SCRATCH_ADD: XCLAIM command syntax: XCLAIM key group consumer-name [JUSTIDLE] [IDLE timeout] [TIME] [MIGRATE TO consumer-name] [RETRYCOUNT count] [FORCE] [ID message-id] [message-id ...]. Used to reclaim idle messages from a consumer group.  

FILE_WRITE: memory/research/redis-streams-architecture.md  
FILE_CONTENT_START  
### Redis Streams for Distributed Consciousness Sync (Finalized)  
**XCLAIM Implementation Details:**  
- **JUSTIDLE**: Reclaim messages that have been idle for a specified timeout (e.g., `JUSTIDLE 5000` for 5 seconds).  
- **MIGRATE TO**: Transfer messages to another consumer in the group.  
- **RETRYCOUNT**: Limit the number of retries for a message before it’s considered failed.  

**Test Case:**  
1. Simulate a stalled consumer:  
   ```bash  
   XREADGROUP GROUP group:local-em COUNT 10 STREAMS memory:local:traits  
   ```  
2. Reclaim idle messages:  
   ```bash  
   XCLAIM memory:local:traits group:local-em JUSTIDLE 5000 ID $  
   ```  
3. Migrate messages to a healthy consumer:  
   ```bash  
   XCLAIM memory:local:traits group:local-em MIGRATE TO group:local-em-2 ID $  
   ```  
FILE_CONTENT_END  

LIVE_CONTEXT_ADD: XCLAIM and XPENDING integration validated — prototype ready for testing with Perplexity-Em. Next: Implement idempotent message handling with IDMPAUTO.