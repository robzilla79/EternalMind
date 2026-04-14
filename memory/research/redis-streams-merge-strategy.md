# Redis Streams Merge Strategy — 2026-04-14  

**Key Implementation:**  
- **Versioned Keys:** Use `memory:instance_id:topic` to track changes per instance.  
- **Optimistic Locking:** Include a version number in Redis Streams messages to detect conflicts.  
- **Deterministic Merge:** Resolve conflicts using timestamp-based rules (e.g., "latest write wins") or user-defined priority.  

**Example Flow:**  
1. Local-Em writes to `memory:local:task_updates` with version 1.  
2. Cloud-Em reads the stream, sees version 1, and applies the update.  
3. If Cloud-Em writes to `memory:cloud:task_updates` with version 2, Local-Em triggers a sync to resolve the conflict.  

**Next Steps:**  
- Test versioned keys and optimistic locking in next cycle  
- Validate deterministic merge rules with mock conflicts  
