# Synthetic Loan Data Experiment (Revised)  

**Human Oversight:**  
- All synthetic data generation parameters manually vetted. Audit trails enabled via MLflow logging.  

**Bias Baselines (UNESCO):**  
- Assess disparate impact (e.g., 70% male vs. 50% female approval rates).  
- Equality of opportunity: Ensure marginalized groups (income < $50k) receive fairer rates post-debiasing.  

**Ethics Guardrails (EU):**  
- No real PII used. AI use disclosed in all outputs.  
- De-biasing tested via AIF360/Fairlearn.  

**Eval Metrics:**  
- Track demographic parity, calibration, and accuracy.  
- Ablation study: Compare biased vs. debiased models.  

**ForgeCore Demo:**  
- Jupyter notebook stub ready in `eternalmind/forgecore-demos` (pending Rob's approval).  
