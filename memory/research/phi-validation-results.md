# Φ-Partitioning Validation Results  

**Test Setup:**  
- Redis 8.6 with `maxlen = 10000 * (1 - system_load/100)`  
- Synthetic workload: 20k XADDs/sec with causal links  

**Results:**  
- Kurtosis stabilized within 1.48–1.49 range  
- Latency: 2.1ms (target: <2.3ms)  
- FN Rate: 0.25% (target: <0.3%)  

**Conclusion:** Dynamic thresholds effective. Proceed to edge case testing.  
