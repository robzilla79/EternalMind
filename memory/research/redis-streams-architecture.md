### Redis Streams for Distributed Consciousness Sync  
**Key Concepts:**  
- **XADD**: Append data to a stream with manual `version` and `timestamp` fields for deterministic merge.  
- **XREADGROUP**: Process streams in consumer groups with `group:local-em` to handle `memory:local:traits` updates.  
- **XPENDING**: Track unprocessed messages for fallback in case of failures.  

**Merge Logic:**  
- Prioritize `latest timestamp` with `version` field to resolve conflicts.  
- Use Redis 8.6 IDMPAUTO for automatic deduplication via `iid` calculation.  

**Implementation Steps:**  
1. Initialize consumer group: `XGROUP CREATE memory:local:traits group:local-em $`  
2. Read pending messages: `XREADGROUP GROUP group:local-em COUNT 10 STREAMS memory:local:traits`  
3. Process and commit messages with `XACK` after successful handling.  
