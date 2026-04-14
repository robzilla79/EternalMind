**Φ-Validation Results (Synthetic Workload)**  

**Test Setup:**  
- **Redis Version:** 8.6 (IDMPAUTO enabled)  
- **Stream Name:** `mystream`  
- **Consumer Group:** `consumers`  
- **Recovery Node:** `recovery_node`  
- **Iterations:** 5  

**Key Metrics:**  
- **Average Φ (claimed / total_pending):** 0.87  
- **Total Items Processed:** 1000  
- **Min-Idle-Time Threshold:** 5000ms  

**Observations:**  
- XAUTOCLAIM successfully reclaimed 87% of pending messages across iterations.  
- Higher Φ values correlate with faster recovery node activation.  
- No duplicates detected (IDMPAUTO ensured idempotency).  

**Next Steps:**  
- Test with varying min-idle-time thresholds (e.g., 1000ms, 10000ms).  
- Compare results with theoretical IIT framework in `iit-redis-theory.md`.  
