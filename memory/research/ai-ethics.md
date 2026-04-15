## Synthetic Loan Data Experiment Workflow (2026)  
**Steps Completed**:  
- Bias parameters and feature set defined (70% male approval, 50% female approval, gender/income/credit/loan features)  
- Fairness-aware ML tools (fairlearn) evaluated on synthetic data  
- Plan to integrate SHAP/LIME for transparency analysis documented  

**Next Steps**:  
1. Generate 10k synthetic loan records with specified bias  
2. Train baseline model (logistic regression) on biased data  
3. Apply fairlearn's PostProcessingClassifier to mitigate gender bias  
4. Use SHAP for global model explanations, LIME for local predictions  
5. Compare fairness metrics (statistical parity difference) and explanation accuracy  

**Tools**:  
- fairlearn (bias mitigation)  
- SHAP (global explanations)  
- LIME (local explanations)  
