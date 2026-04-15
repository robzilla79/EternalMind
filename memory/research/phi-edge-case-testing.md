# Φ-Partitioning Edge Case Testing Plan  

**Test Scenarios:**  
1. **Extreme PSA Values (PHI <23.85, >142.9):**  
   - Validate NPV/PPV thresholds using synthetic datasets.  
   - Monitor kurtosis drift in `phi_validation_stream`.  

2. **Biopsy-Naïve Populations:**  
   - Simulate limited validation data with lower sensitivity.  
   - Test dynamic maxlen formula robustness.  

**Tools:**  
- Use `redis_streams_phi_test.py` with modified parameters.  
- Leverage RedisInsight for real-time kurtosis monitoring.  

**Expected Outcomes:**  
- Confirm PHI <27 as strong negative predictor (NPV 93-96%).  
- Ensure system_load adjustments maintain stability in sparse datasets.  
