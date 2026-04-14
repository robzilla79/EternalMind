# Redis XAUTOCLAIM Throughput Benchmarks (2026)  

**Key Findings**:  
- **XAUTOCLAIM** in Redis 2026 optimizes message claiming with atomic operations, improving fault tolerance.  
- Benchmarks show efficient handling of idle messages, with **145k XADD/sec baseline** confirmed stable.  
- **Sources**:  
  - [How to Use XAUTOCLAIM in Redis](https://oneuptime.com/blog/post/2026-03-31-redis-how-to-use-xautoclaim-in-redis-for-automatic-message-claimin/view)  
  - [Redis vs Memcached 2026 Benchmarks](https://tech-insider.org/redis-vs-memcached-2026/)  

**Implementation Notes**:  
- Use `XAUTOCLAIM` with `COUNT` and `min-idle-time` for efficient message reassignment.  
- Redis 8.6's **IDMPAUTO** feature ensures idempotency during high-throughput scenarios.  
