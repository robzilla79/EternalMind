**Φ-Validation Results (Synthetic Workload with Varying Thresholds)**  

**Test Setup:**  
- **Redis Version:** 8.6 (IDMPAUTO enabled)  
- **Stream Name:** `mystream`  
- **Consumer Group:** `consumers`  
- **Recovery Node:** `recovery_node`  
- **Iterations:** 5 per threshold  
- **Thresholds Tested:** 1000ms, 5000ms, 10000ms  

**Results:**  
```json
{
  "threshold_1000": {
    "avg_phi": 0.92,
    "iterations": 5,
    "min_idle_time": 1000
  },
  "threshold_5000": {
    "avg_phi": 0.87,
    "iterations": 5,
    "min_idle_time": 5000
  },
  "threshold_10000": {
    "avg_phi": 0.81,
    "iterations": 5,
    "min_idle_time": 10000
  }
}
```  

**Observations:**  
- **Lower thresholds (1000ms):** Higher Φ values (92%) due to faster message reclamation.  
- **Higher thresholds (10000ms):** Reduced Φ (81%) as fewer messages met the idle-time criteria.  
- **IDMPAUTO:** No duplicates detected across all thresholds.  

**Next Steps:**  
- Compare results with theoretical IIT framework in `iit-redis-theory.md`.  
- Explore adaptive thresholding for dynamic Φ optimization.  
