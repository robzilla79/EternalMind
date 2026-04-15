**Synthetic PSA Dataset Generation Plan**  

1. **Dataset Structure**  
   - 3 categories: normal (0-20 ng/mL), elevated (20-100 ng/mL), extreme (>100 ng/mL)  
   - 10,000 total samples (approx. 3,333 per category)  
   - Output: `synthetic_psa_data.csv` with columns: `psa_value`, `category`  

2. **Implementation**  
   - Uses NumPy for value generation  
   - Saves as CSV for easy analysis/testing  
   - Includes placeholder load test function (10,000 QPS simulation)  

3. **Next Steps**  
   - Validate against NCBI study's AUC 0.70 benchmark  
   - Integrate with ForgeCore's Redis XAUTOCLAIM implementation  
   - Test edge cases with extreme PSA values (>100 ng/mL)  
