# Real-Time AUC Monitoring via RedisInsight  

**Steps to Validate:**  
1. **Stream Length Check:**  
   Use `XINFO STREAM phi_validation_stream` to confirm 1,000 entries are present.  

2. **Entity Extraction Verification:**  
   Sample entries using `XREAD` to ensure `entities` field contains correctly labeled spaCy output.  

3. **AUC Calculation:**  
   Use RedisInsight's query tools to compute AUC against NCBI baseline (0.70). Target: 0.72 uplift.  

4. **Kurtosis Alert Setup:**  
   Configure RedisInsight to trigger alerts if kurtosis exceeds 1.55.  

**Next:** Execute `XINFO STREAM phi_validation_stream` to confirm data integrity.  
