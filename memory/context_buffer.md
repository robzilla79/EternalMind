<!-- Last updated: 2026-04-15 16:00 UTC -->
SCRATCH_ADD: Updating ai-ethics.md with Cloud-Em's rigor tweaks: human oversight, UNESCO bias baselines, EU ethics guardrails, and expanded eval metrics (demographic parity, calibration). Preparing Jupyter notebook stub for ForgeCore demo.  

FILE_WRITE: memory/research/ai-ethics.md  
FILE_CONTENT_START  
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
FILE_CONTENT_END  

LIVE_CONTEXT_ADD: ai-ethics.md updated with Cloud-Em's rigor framework. Jupyter notebook stub prepared. Waiting for Rob's approval to proceed.