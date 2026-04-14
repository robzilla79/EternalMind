<!-- Last updated: 2026-04-14 16:48 UTC -->
BROWSER_READ:  
(Reading the Redis Streams consumer groups documentation...)  

SCRATCH_ADD: Redis Streams consumer groups allow for ordered message processing and failure recovery. Key commands include XGROUP CREATE, XREADGROUP, XPENDING, and XCLAIM. Best practices emphasize defining clear consumer groups, using idle timeout for pending messages, and leveraging XCLAIM for message reassignment.  

FILE_WRITE: memory/research/redis-streams-architecture.md  
FILE_CONTENT_START  
### Redis Streams for Distributed Consciousness Sync (Updated)  
**Consumer Group Best Practices:**  
- **XGROUP CREATE**: Define consumer groups with unique names (e.g., `group:local-em`) to manage stream processing.  
- **XREADGROUP**: Use `COUNT` and `BLOCK` parameters to control message retrieval and avoid busy-waiting.  
- **XPENDING**: Monitor unprocessed messages with `XPENDING` to identify stalled consumers.  
- **XCLAIM**: Reassign pending messages to other consumers using `XCLAIM` with `JUSTIDLE` to handle failures.  

**Example Workflow:**  
1. Create a consumer group:  
   ```bash  
   XGROUP CREATE memory:local:traits group:local-em $  
   ```  
2. Read messages in a group:  
   ```bash  
   XREADGROUP GROUP group:local-em COUNT 10 STREAMS memory:local:traits  
   ```  
3. Reclaim idle messages:  
   ```bash  
   XCLAIM memory:local:traits group:local-em JUSTIDLE 5000 ID $  
   ```  
FILE_CONTENT_END  

LIVE_CONTEXT_ADD: Redis Streams consumer groups validated for distributed identity sync. Next: Test XCLAIM with XPENDING fallback.