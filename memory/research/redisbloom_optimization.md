**RedisBloom Optimization Parameters**  
- False positive rate can be set during Bloom filter creation using:  
  `RedisBloom.CONFIG SET <filter-name> capacity <size> error <rate>`  
- Recommended error rates:  
  - 0.01% for critical duplicate detection  
  - 0.1% for general use cases  
- Memory usage formula:  
  `Memory = (capacity × log(1/error)) / (ln(2)^2)`  
