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
