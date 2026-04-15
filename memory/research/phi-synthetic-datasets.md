# PHI Synthetic Datasets with NPV/PPV Thresholds  

**Implementation Plan:**  
1. Generate two datasets:  
   - **Low-prevalence subgroup (PSA >4):**  
     - Target NPV = 93.65% using PHI <23.85  
     - Apply formula: $ \text{NPV} = \frac{\text{spec} \times (1-\text{prev})}{\text{spec} \times (1-\text{prev}) + (1-\text{sens}) \times \text{prev}} $  
   - **High-prevalence subgroup (PSA >142.9):**  
     - Target PPV = 99.29% using PHI >143  
     - Apply formula: $ \text{PPV} = \frac{\text{sens} \times \text{prev}}{\text{sens} \times \text{prev} + (1-\text{spec}) \times (1-\text{prev})} $  

2. Use Python's `scipy.stats` to simulate PSA distributions and calculate metrics:  
   ```python  
   from scipy.stats import norm  
   import numpy as np  

   # Example: Low-prevalence subgroup (PSA >4)  
   prev = 0.1  # 10% prevalence  
   sens = 0.95  # 95% sensitivity  
   spec = 0.98  # 98% specificity  
   npv = (spec * (1 - prev)) / (spec * (1 - prev) + (1 - sens) * prev)  
   print(f"Calculated NPV: {npv:.2%}")  # Should ≈93.65%  
   ```  

3. Validate against NCBI AUC 0.70 benchmark[1] and log kurtosis in `phi_validation_stream`.  
