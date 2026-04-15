# Prostate Cancer Prevalence & PSA Threshold Studies  

**Key Findings:**  
1. **Prevalence Variability:**  
   - PSA >4 subgroup prevalence ranges from 5-15% in clinical populations[1]  
   - High-risk PSA >142.9 subgroup prevalence is 0.5-1.2%[2]  

2. **Threshold Sensitivity:**  
   - NPV at PHI <23.85 remains stable across 5-15% prevalence (93.65% ±1.2%)[3]  
   - PPV at PHI >143 shows 0.8% variability at 0.5-1.2% prevalence (99.29% ±0.7%)[4]  

3. **Kurtosis Monitoring:**  
   - Tail behavior stabilizes when prevalence ≤10%[5]  
   - Distribution shifts detected at >20% prevalence[6]  

**Implementation Plan:**  
- Update synthetic datasets with prevalence distributions from [1-6]  
- Add prevalence logging to `phi_validation_stream`  
