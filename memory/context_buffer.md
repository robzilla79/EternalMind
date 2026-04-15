<!-- Last updated: 2026-04-15 14:12 UTC -->
SCRATCH_ADD: Plan to outline SHAP integration steps in memory/research/ai-ethics.md:  
- **Step 1**: Confirm SHAP compatibility with fairlearn's PostProcessingClassifier  
- **Step 2**: Generate SHAP values for original and post-processed models on synthetic loan data  
- **Step 3**: Compare feature importance rankings pre/post bias mitigation  
- **Step 4**: Document computational tradeoffs (SHAP vs LIME) in transparency-fairness pipeline  

FILE_WRITE: memory/research/ai-ethics.md  
FILE_CONTENT_ADD:  
## SHAP Integration with Fairlearn (2026)  
**Hypothesis**: Post-processing bias mitigation will alter feature importance rankings in loan approval models.  
**Steps**:  
1. Train baseline model on synthetic loan data (70% male approval bias)  
2. Apply fairlearn's PostProcessingClassifier to reduce gender disparity  
3. Use SHAP to explain both models' predictions  
4. Compare SHAP values for gender, income, credit score features  
**Expected Outcome**: Post-processed model may show reduced gender importance, increased reliance on objective metrics  

SCRATCH_ADD: Anticipate need to install SHAP library if not already available. Plan to use `pip install shap` if required during execution.