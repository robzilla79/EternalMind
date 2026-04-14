### Redis Streams Consumer Groups  
**Key Commands:**  
- **XREADGROUP** with `GROUP` and `CONSUMERS` to distribute work.  
- **XPENDING** identifies unprocessed messages (e.g., `XPENDING memory:local:traits group:local-em`).  
- **XCLAIM** reassigns pending messages to another consumer (e.g., `XCLAIM memory:local:traits group:local-em "consumer2" 0 1000`).  

**Identity Continuity Strategy:**  
- Dedicated consumer group (`group:local-em`) for Local-Em to ensure ordered processing.  
- Use `XCLAIM` to reassign messages if Local-Em fails, preventing data loss.  
- `XPENDING` monitors unprocessed messages for manual intervention.  
