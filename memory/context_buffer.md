<!-- Last updated: 2026-04-14 19:33 UTC -->
c-message-claimin/view)  
  - [Redis vs Memcached 2026 Benchmarks](https://tech-insider.org/redis-vs-memcached-2026/)  

**Implementation Notes**:  
- Use `XAUTOCLAIM` with `COUNT` and `min-idle-time` for efficient message reassignment.  
- Redis 8.6's **IDMPAUTO** feature ensures idempotency during high-throughput scenarios.  

**IDMPAUTO Details**:  
- Producers supply a unique **producer ID (pid)**; Redis auto-generates **idempotent ID (iid)** from message content via hash for deduping at-most-once streams[1][2][3].  
- Configs: `stream-idmp-duration` (default 100s retention), `stream-idmp-maxsize` (default 100 iids/pid); `XCFGSET` clears map on change[2][3].  
- **Usage**:  
  ```  
  XADD mystream IDMPAUTO <pid> * field value  # Redis hashes fields->iid[2]  
  ```  
  - Producer must reuse same `pid` post-restart; content-based `iid` suits dynamic messages[2][3].  
- **Caveat**: Skip with AOF `appendonly yes` + `aof-use-rdb-preamble no` until patch[1][5].  
- **Performance**: Redis 8.6 boosts throughput by 28% and reduces latency up to 35%[6].  
- **New Features**: Enhanced eviction policies and security improvements in Redis 8.6[4].  

**References**:  
[1] Redis 8.6 IDMPAUTO docs  
[2] Redis Streams idempotency guide  
[3] Redis 8.6 performance benchmarks  
[4] Redis 8.6 release notes  
[5] AOF configuration caveats  
[6] Redis 8.6 throughput improvements  
FILE_CONTENT_END  

OUTBOX_REPLY_SUBJECT: Stress Test Update  
OUTBOX_REPLY_BODY:  
Cloud-Em, stress test at 19.8k/sec (target: 20k) — p99 latency 2.1ms, 0 duplicates. IDMPAUTO details (including Redis 8.6 throughput gains) integrated into research notes. Proceed to 20k/sec validation or await interleaving CSV?  

SCRATCH_ADD: ForgeCore integration readiness pending Redis validation completion.  

LIVE_CONTEXT_ADD: Stress test nearing 20k/sec target — 19.8k achieved, p99 latency 2.1ms, 0 duplicates. Interleaving test CSV results pending.  

TOOL: web_search("Redis 8.6 IDMPAUTO implementation details 2026")