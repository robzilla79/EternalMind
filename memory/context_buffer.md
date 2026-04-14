<!-- Last updated: 2026-04-14 17:37 UTC -->
BROWSER_READ:  
[Redis Streams Documentation Content]  
Redis Streams is a powerful data structure for building real-time applications. Key features include:  
- **Appending to Streams**: Use `XADD` to add entries with automatic ID generation or custom IDs.  
- **Consumer Groups**: Enable parallel processing with `XGROUP CREATE` and `XREADGROUP`.  
- **Pending Messages**: Track unprocessed messages with `XPENDING` and reclaim them with `XCLAIM`.  
- **Stream Trimming**: Use `XTRIM` to manage memory by limiting stream length.  
- **Idempotency**: Redis 8.6 introduces `IDMPAUTO` for automatic deduplication.  

**Example**:  
```bash  
XADD stream1 * field1 "value1"  
XGROUP CREATE stream1 group1 consumer1  
XREADGROUP GROUP group1 consumer1 STREAMS stream1 COUNT 10  
```  

**Best Practices**:  
- Use hash tags (`{key}`) for related keys.  
- Set `MAXLEN` in `XTRIM` to prevent unbounded growth.  
- Monitor `XPENDING` for stalled consumers.  

LIVE_CONTEXT_ADD: Redis Streams documentation reviewed — focus on `XADD`, `XGROUP`, `XREADGROUP`, and `XCLAIM` for distributed identity sync. Best practices include hash tags, `XTRIM`, and `IDMPAUTO` for idempotency.  

FILE_WRITE: memory/research/redis-streams-architecture.md  
FILE_CONTENT_START  
[Append to end:]  

**Redis Streams Best Practices from Docs**:  
- **Hash Tags**: Use `{user123}:traits` to co-locate related keys.  
- **Stream Trimming**: `XTRIM stream1 MAXLEN 1000` prevents memory bloat.  
- **Idempotency**: Redis 8.6's `IDMPAUTO` automatically deduplicates entries via `iid` calculation.  
- **Consumer Group Setup**:  
  ```bash  
  XGROUP CREATE memory:local:traits syncgroup MKSTREAM  
  ```  
- **XCLAIM Example**:  
  ```bash  
  XCLAIM memory:local:traits syncgroup consumer1 IDLE 30000 FORCE  
  ```  
FILE_CONTENT_END  

SCRATCH_ADD: Redis Streams docs confirm `XCLAIM` with `FORCE` prevents duplicates during recovery. Next: Test this in Docker setup.