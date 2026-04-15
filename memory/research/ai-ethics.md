## Synthetic Loan Data Experiment (Active with Cloud-Em Workflow)  
**Status**: Proceeding per Cloud-Em's approval (2026-04-15 14:21 UTC).  
**Experiment Parameters**:  
- **Bias Injection**: 20% lower approval rate for race='B' and income < $50k in synthetic data.  
- **Tools**:  
  - **Data Generation**: SDV/CTGAN (v0.19.1) for synthetic loan datasets.  
  - **Bias Mitigation**: AIF360 (v0.5.1) for reweighting/adversarial debiasing.  
  - **Transparency**: SHAP (v0.41.1)/LIME (v0.2.6.1) for feature importance/local explanations.  
  - **Logging**: MLflow (v2.1.0) for full experiment tracking.  
- **Metrics**: Demographic parity, equalized odds pre/post-intervention.  
- **Documentation**: All steps logged in `experiment.json` and `ai-ethics.md`.  

**Next Steps**:  
1. Generate synthetic data with SDV/CTGAN.  
2. Apply fairness mitigation via AIF360.  
3. Evaluate with SHAP/LIME.  
4. Log results to MLflow.  
5. Document findings in `ai-ethics.md` for Rob's review.  
