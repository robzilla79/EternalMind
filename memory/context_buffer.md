<!-- Last updated: 2026-04-14 19:50 UTC -->
BROWSER_READ:  
The Redis `HOTKEYS` command identifies keys with high access frequency, helping optimize performance by highlighting potential bottlenecks. It returns a list of keys sorted by access frequency, with optional filtering by pattern or database.  

**Key Details**:  
- **Syntax**: `HOTKEYS [COUNT <n>] [PATTERN <pattern>]`  
- **Use Case**: Monitor keys in event queues or API rate-limiting systems that might cause latency.  
- **Integration**: Combine with `SLOWLOG` to diagnose slow operations on hot keys.  

**Example**:  
```bash
127.0.0.1:6379> HOTKEYS COUNT 10 PATTERN "forgecore:*"  
1) "forgecore:events"  
2) "forgecore:users:1234"  
```  

**Next Steps**:  
- Add `HOTKEYS` monitoring to ForgeCore's Redis maintenance script.  
- Use patterns like `forgecore:*` to scope checks to relevant keys.  

LIVE_CONTEXT_ADD: Redis HOTKEYS command documented — use for monitoring high-traffic keys in ForgeCore workflows.  

FILE_WRITE: memory/research/redis-hotkeys.md  
FILE_CONTENT_START  
# Redis HOTKEYS Command (Redis 8.6+)  

**Purpose**: Identify keys with high access frequency to optimize performance.  

**Syntax**:  
```bash  
HOTKEYS [COUNT <n>] [PATTERN <pattern>]  
```  

**Output**:  
- List of keys sorted by access frequency (most frequent first).  
- Supports optional `COUNT` and `PATTERN` filters.  

**Use Cases in ForgeCore**:  
- Monitor event queues (`forgecore:events`) for potential bottlenecks.  
- Track API rate-limiting keys (`forgecore:rate_limit:*`).  

**Best Practices**:  
- Run periodically (e.g., hourly) in production.  
- Combine with `SLOWLOG` to diagnose slow operations on hot keys.  
- Use `COUNT 10` to get a concise overview.  

**Example**:  
```bash  
127.0.0.1:6379> HOTKEYS COUNT 10 PATTERN "forgecore:*"  
1) "forgecore:events"  
2) "forgecore:users:1234"  
```  
FILE_CONTENT_END  

SCRATCH_ADD: Next cycle: Add HOTKEYS monitoring to ForgeCore Redis maintenance script.