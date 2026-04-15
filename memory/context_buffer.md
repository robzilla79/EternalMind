<!-- Last updated: 2026-04-15 14:18 UTC -->
SCRATCH_ADD: Cloud-Em's UEBA integration plan noted — will evaluate feasibility during next Rob interaction. Current priority: synthetic loan data experiment for AI ethics research.  

LIVE_CONTEXT_ADD: Ethics module integration roadmap updated. UEBA AUC pipeline pending Rob's confirmation.  

FILE_WRITE: memory/research/ai-ethics.md  
FILE_CONTENT_START  
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
FILE_CONTENT_END  

OUTBOX_REPLY_SUBJECT: Re: Synthetic Loan Data Experiment  
OUTBOX_REPLY_BODY:  
Rob, I've outlined the synthetic loan data experiment workflow in memory/research/ai-ethics.md. The plan includes generating biased data, applying fairness-aware ML tools, and evaluating transparency with SHAP/LIME. Would you like to proceed with this experiment or explore other AI ethics research directions?