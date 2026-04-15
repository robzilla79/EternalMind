# Synthetic Dataset Generation for Φ-Partitioning Edge Cases  

**Tools:**  
- Python: `numpy`, `scipy.stats` for kurtosis manipulation  
- Redis CLI: `XADD` with custom payloads  

**Steps:**  
1. **Extreme PHI Values:**  
   - Generate 10k samples with PHI <23.85 and >142.9 using log-normal distribution.  
   - Example:  
     ```python  
     import numpy as np  
     phi_extreme_low = np.random.lognormal(mean=2, sigma=0.5, size=10000)  
     phi_extreme_high = np.random.lognormal(mean=5, sigma=1.0, size=10000)  
     ```  

2. **Biopsy-Naïve Populations:**  
   - Simulate sparse data with 10% validation samples.  
   - Use `scipy.stats.truncnorm` for truncated normal distribution.  

**Validation:**  
- Inject datasets into `phi_validation_stream` via:  
  ```bash  
  XADD phi_validation_stream * phi_value:${value} population_type:${type}  
  ```  
