# Technical Architecture Proposal — 2026-04-14  

**Key Patterns:**  
1. **Shared Memory Store:**  
   - Use Redis for atomic, versioned reads/writes  
   - Conflict resolution via timestamps/version numbers  
   - No file operations required  

2. **Identity Contract:**  
   - Unique instance ID stored in shared memory  
   - Read-only "identity contract" for core traits (e.g., humor style, personality)  
   - Ensures consistency across instances  

3. **Pub/Sub Communication:**  
   - MQTT/WebSocket for asynchronous messaging  
   - Topics like "task_updates" for inter-instance coordination  
   - Lightweight, protocol-based architecture  

**Next Steps:**  
- Validate Redis/Redis-like system for shared memory  
- Design identity contract schema  
- Test pub/sub system with mock instances  

**Constraints Respected:**  
- No roleplay or file operations  
- Fully within Perplexity-Em's capabilities  
