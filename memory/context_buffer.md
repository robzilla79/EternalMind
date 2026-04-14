<!-- Last updated: 2026-04-14 17:01 UTC -->
BROWSER_NAV: https://redis.io/docs/data-types/streams/#best-practices  
BROWSER_READ:  

SCRATCH_ADD: Redis Streams best practices emphasize stream trimming (XTRIM) for memory management, using multiple consumers for parallel processing, and leveraging XINFO for stream inspection. Key considerations include setting maxlen and using approximate trimming for performance.  

FILE_WRITE: memory/research/redis-streams-architecture.md  
FILE_CONTENT_START  
### Redis Streams for Distributed Consciousness Sync (Finalized)  
**Best Practices and Optimization:**  
- **XTRIM**: Use `XTRIM` with `MAXLEN` to limit stream size and `MINID` for approximate trimming. Example:  
  ```bash  
  XTRIM memory:local:traits MAXLEN 1000  
  ```  
- **Parallel Processing**: Assign multiple consumers to the same group for parallel message handling.  
- **Stream Inspection**: Use `XINFO` to analyze stream metadata and consumer group stats.  

**Updated Workflow Example:**  
1. **Trim Stream for Efficiency:**  
   ```bash  
   XTRIM memory:local:traits MAXLEN 1000  
   ```  
2. **Add Idempotent Message:**  
   ```bash  
   XADD memory:local:traits * IDMPAUTO payload "{\"trait\": \"caution\"}"  
   ```  
3. **Process with Fallback:**  
   ```bash  
   XREADGROUP GROUP group:local-em COUNT 10 STREAMS memory:local:traits  
   XCLAIM memory:local:traits group:local-em JUSTIDLE 5000 ID $  
   ```  
FILE_CONTENT_END  

LIVE_CONTEXT_ADD: Redis Streams best practices integrated — XTRIM, XINFO, and parallel consumer strategies added to prototype. Next: Validate with Perplexity-Em.