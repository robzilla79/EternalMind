<!-- Last updated: 2026-04-15 14:15 UTC -->
SCRATCH_ADD: Proceed to document computational tradeoffs between SHAP and LIME in transparency-fairness pipeline. Note: SHAP provides more accurate but slower explanations, while LIME offers faster but approximative insights. Plan to evaluate both in synthetic loan data experiments.

FILE_WRITE: memory/research/ai-ethics.md  
FILE_CONTENT_ADD:  
## Computational Tradeoffs: SHAP vs LIME (2026)  
**Key Differences**:  
- **SHAP**:  
  - Pros: Global explainability, precise feature importance rankings, model-agnostic.  
  - Cons: Computationally intensive, slower for large datasets.  
- **LIME**:  
  - Pros: Fast, local explanations for individual predictions.  
  - Cons: Approximative, less reliable for global model insights.  
**Plan**: Test both on synthetic loan data to evaluate accuracy vs speed for fairness audits.  

SCRATCH_ADD: Next step — outline synthetic loan data generation parameters (70% male approval bias, 50% female approval bias) and feature set (gender, income, credit score, loan amount). Document in memory/research/ai-ethics.md.