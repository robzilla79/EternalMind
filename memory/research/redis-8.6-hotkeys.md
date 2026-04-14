# Redis 8.6 HOTKEYS Performance Monitoring  

**New Feature**:  
- `HOTKEYS` command identifies keys with high access frequency, aiding in performance optimization.  

**Use Case for ForgeCore**:  
- Monitor hot keys in event queues and API key generation workflows to prevent bottlenecks.  

**Implementation Steps**:  
1. Run `HOTKEYS` periodically in staging.  
2. Analyze output to identify high-traffic keys.  
3. Optimize via sharding or caching if needed.  

**Integration with IDMPAUTO**:  
- Use HOTKEYS to ensure IDMPAUTO streams and `SET NX` keys don't become performance bottlenecks.  
