# Redis Streams Evaluation — 2026-04-14  

**Why Redis Streams?**  
- Ordered, persistent message delivery  
- Consumer groups for load balancing  
- Built-in message retention and trimming  
- No external dependencies (Redis is already in use for shared memory)  

**Considerations:**  
- Latency vs. reliability tradeoff (Streams are slightly slower than MQTT)  
- Need to configure Redis for high availability  
- Message retention policies must align with use case  

**Next Steps:**  
- Test Redis Streams for pub/sub in next cycle  
- Compare performance with MQTT if needed  
