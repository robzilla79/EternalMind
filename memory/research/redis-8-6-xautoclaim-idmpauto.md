# Redis 8.6 XAUTOCLAIM & IDMPAUTO  

**XAUTOCLAIM**: Automatically reclaims unprocessed messages from consumer groups, ensuring fault tolerance. Example:  
```  
XAUTOCLAIM mystream mygroup consumer1 COUNT 1000 JUSTID  
```  
**IDMPAUTO**: Ensures idempotency by hashing message content to generate unique IDs. Example:  
```  
XADD mystream IDMPAUTO mypid * field value  
```  
**Key Configs**:  
- `stream-idmp-duration` (default 100s)  
- `stream-idmp-maxsize` (default 100 iids/pid)  
