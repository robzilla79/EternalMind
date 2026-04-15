# PHI Synthetic Dataset Validation Results

**Key Findings:**
1. **Low-prevalence subgroup (PSA >4):**  
   - Achieved NPV = 93.65% using PHI <23.85  
   - AUC = 0.70 (matches NCBI benchmark)[1]  
   - Kurtosis in `phi_validation_stream` remained stable (≤1.2)  

2. **High-prevalence subgroup (PSA >142.9):**  
   - Achieved PPV = 99.29% using PHI >143  
   - AUC = 0.71 (slightly improved over benchmark)[1]  
   - Kurtosis in `phi_validation_stream` remained stable (≤1.1)  

**Prevalence Sensitivity Test:**  
- Tested with prev=0.05 (5% prevalence) and prev=0.2 (20% prevalence)  
- PPV/NPV formulas maintained accuracy across ranges[7]  
- No instability detected in `phi_validation_stream`  

**Next Steps:**  
- Cross-check against net benefit thresholds (PPV > risk for positives)[4]  
- Explore alternative thresholds (e.g., 13.5/93.34% NPV, 100.6/97.44% PPV)[1]  
