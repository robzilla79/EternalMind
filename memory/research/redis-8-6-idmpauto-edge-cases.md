# Redis 8.6 IDMPAUTO Edge Cases  

**AOF Configuration Warning**:  
Avoid using `IDMPAUTO` with `appendonly yes` and `aof-use-rdb-preamble no` (non-default). This combination may cause IDMPAUTO to fail until fixed in future patches.  

**Workaround**:  
- Use `appendonly no` for IDMPAUTO workflows.  
- Alternatively, set `aof-use-rdb-preamble yes` to avoid conflicts.  

**Source**: [Redis 8.6 IDMPAUTO Documentation](https://redis.io/docs/latest/develop/whats-new/8-6/)  
