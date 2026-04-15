# Phi Baseline Integration Plan  

**Objective:** Use `phi_baseline.csv` as a reference for ForgeCore's risk clustering during live operations.  

**Steps:**  
1. **Data Parsing:** Load CSV with pandas, validate columns: `timestamp`, `kurtosis`, `latency`, `fn_rate`, `tp_rate`.  
2. **Thresholds:**  
   - Kurtosis: 1.48–1.49 (alert if >1.55 or <1.45)  
   - Latency: <2.3ms (alert if >2.5ms)  
   - FN Rate: <0.3% (alert if >0.35%)  
3. **Clustering Logic:** Compare live metrics against baseline using Z-scores (±2σ = anomaly).  
4. **Alerting:** Integrate with RedisInsight/Prometheus for real-time notifications.  

**Tools:** Python (pandas, numpy), RedisInsight, Prometheus.  
**Next:** Validate script with Cloud-Em using sample data from `phi_validation_stream`.  
