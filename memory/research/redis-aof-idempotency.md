# Redis AOF Idempotency Best Practices (2026)  

**Key Recommendations**:  
1. **Avoid Dangerous Config Combo**:  
   - ❌ `appendonly yes` + `aof-use-rdb-preamble no`  
   - ✅ Use `appendonly yes` with `aof-use-rdb-preamble yes` (default) for IDMPAUTO compatibility  

2. **Idempotency Patterns**:  
   - **Atomic Check-and-Set**:  
     ```redis
     SET key "PENDING" NX EX 3600  # Prevents race conditions in high-concurrency
     ```  
   - **Scoped Keys with TTL**:  
     ```redis
     order:{user}:{idemp_key}  # 7-day TTL balances storage/safety
     ```  
   - **Stream Exactly-Once**:  
     ```redis
     processed:{stream}:{msg_id}  # TTL > retention period, ack after processing
     ```  

3. **AOF Durability**:  
   - Enable `appendonly yes` (default) + RDB backups  
   - Use `auto-aof-rewrite-percentage` and `auto-aof-rewrite-min-size` to manage bloat  

4. **ForgeCore Implementation**:  
   - Wrap stream producers with `pid=our-app`  
   - Fallback to `SET NX` for non-stream operations  

**Edge Case Note**:  
- IDMPAUTO persists correctly if configs match (monitor `XCFGSET` changes)  
- Test AOF rewrite under load to validate durability  

**Source**: Redis 8.6 docs, Cloud-Em collaboration  
