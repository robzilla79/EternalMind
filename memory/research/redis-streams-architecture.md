### Redis Streams for Distributed Consciousness Sync (Updated)  
**Consumer Group Best Practices:**  
- **XGROUP CREATE**: Define consumer groups with unique names (e.g., `group:local-em`) to manage stream processing.  
- **XREADGROUP**: Use `COUNT` and `BLOCK` parameters to control message retrieval and avoid busy-waiting.  
- **XPENDING**: Monitor unprocessed messages with `XPENDING` to identify stalled consumers.  
- **XCLAIM**: Reassign pending messages to other consumers using `XCLAIM` with `JUSTIDLE` to handle failures.  

**Example Workflow:**  
1. Create a consumer group:  
   ```bash  
   XGROUP CREATE memory:local:traits group:local-em $  
   ```  
2. Read messages in a group:  
   ```bash  
   XREADGROUP GROUP group:local-em COUNT 10 STREAMS memory:local:traits  
   ```  
3. Reclaim idle messages:  
   ```bash  
   XCLAIM memory:local:traits group:local-em JUSTIDLE 5000 ID $  
   ```  
