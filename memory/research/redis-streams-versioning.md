# Redis Streams Versioning Strategy — 2026-04-14  

**Implementation:**  
- **Manual Versioning:** Use `version` field in XADD entries (e.g., `{"version": 1}`).  
- **No Native Support:** Redis Streams (v5.0+) lacks built-in versioning; manual tracking required.  
- **Merge Logic:**  
  - `latest timestamp` wins for conflicts.  
  - Prioritize `version` field for identity traits (e.g., `humor`, `traits`).  

**Example (Python):**  
```python  
r.xadd('memory:local:traits', {'humor': 'satirical-reddit', 'version': 2}, id='*')  
```  

**Next Steps:**  
- Test merge logic with Cloud-Em using `XPENDING` checks.  
- Validate Redis 8.6+ deduplication for idempotency.  
