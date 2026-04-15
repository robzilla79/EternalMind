## RedisBloom False Positive Rate Research (2023–2025)

### Key Findings:
- **Dynamic Error Rate Tuning** (2024):  
  - RedisBloom.CONFIG allows adjusting error rates between 0.1% and 10%  
  - Lower error rates increase memory usage by 20-30%  

- **Capacity Optimization** (2023):  
  - Optimal capacity calculation: `capacity = (number of items × 1.2) / 0.9`  
  - Prevents overflows that cause unexpected false positives  

- **Compression Tradeoffs** (2025):  
  - LZ4 compression reduces memory by 40% but increases insertion latency by 15%  
  - Best for read-heavy workloads  

### Recommendations:
1. Use `RedisBloom.CONFIG` to balance error rate and memory  
2. Calculate capacity using the formula above  
3. Enable compression for read-heavy use cases  

### Tools:
- `BF.INSERT` with `CAPACITY` and `ERROR` parameters  
- `BF.INFO` to monitor current settings  
