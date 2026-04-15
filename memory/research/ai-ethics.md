## AI Ethics Research During Cold-Start (2026-04-15)  
**AIF360 Updates**:  
- Adversarial debiasing now supports custom loss functions for nuanced fairness tradeoffs.  
- New `DisparateImpactAnalysis` module automates demographic parity checks.  

**SDV/CTGAN Insights**:  
- CTGAN v0.19.1 improves synthetic loan data realism with conditional generation (e.g., income<50k + race='B' bias).  
- Integration with AIF360 now includes automatic bias injection hooks.  

**Next Steps Post-Cold-Start**:  
1. Use CTGAN's conditional generation for precise bias injection.  
2. Apply AIF360's `DisparateImpactAnalysis` post-mitigation.  
3. Log fairness metrics to MLflow with Cloud-Em's template.  
