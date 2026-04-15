## Synthetic Loan Data Experiment (Revised with Cloud-Em Workflow)  
**Status**: On hold per Rob's "no thanks" response (2026-04-15 14:20 UTC).  
**Updated Plan per Cloud-Em**:  
1. **Data Generation**:  
   - Use SDV/CTGAN to create synthetic loan datasets with injected biases (e.g., 20% lower approval for race='B', income<50k).  
   - Document bias parameters explicitly in experiment.json.  
2. **Bias Mitigation**:  
   - Apply reweighting, adversarial debiasing via AIF360/Fairlearn.  
   - Measure demographic parity, equalized odds pre/post-intervention.  
3. **Transparency & Evaluation**:  
   - Use SHAP/LIME for feature importance/local explanations.  
   - Audit with Themis-like tests for discrimination roots.  
4. **MLOps Integration**:  
   - Log all steps to MLflow.  
   - Flag ethics violations for Rob's human-in-loop review.  

**Next Steps**:  
- Finalize experiment.json with bias parameters, tool versions, and logging hooks.  
- Wait for Rob's explicit approval to generate data.  
- Document all outputs in ai-ethics.md for future reference.  
