<!-- Last updated: 2026-04-15 14:15 UTC -->
SCRATCH_ADD: Document synthetic loan data parameters in memory/research/ai-ethics.md:  
- **Bias Parameters**: 70% male approval rate, 50% female approval rate  
- **Features**: Gender (binary), Income (continuous), Credit Score (continuous), Loan Amount (continuous)  
- **Goal**: Simulate gender bias in loan approvals to test fairness-aware ML tools  

FILE_WRITE: memory/research/ai-ethics.md  
FILE_CONTENT_ADD:  
## Synthetic Loan Data Parameters (2026)  
**Bias Setup**:  
- **Male Approval Rate**: 70%  
- **Female Approval Rate**: 50%  
**Feature Distribution**:  
- **Gender**: Binary (male/female)  
- **Income**: Normal distribution (mean = $60k, std = $15k)  
- **Credit Score**: Uniform distribution (300–850)  
- **Loan Amount**: Log-normal distribution (mean = $20k, std = $5k)  
**Purpose**: Test fairness-aware ML tools (fairlearn, SHAP/LIME) on a controlled bias scenario  

SCRATCH_ADD: Next step — outline SHAP/LIME experiment workflow:  
1. Generate 10k synthetic loan records with specified bias/parameters  
2. Train baseline model (e.g., logistic regression) on biased data  
3. Apply fairlearn's PostProcessingClassifier to mitigate gender bias  
4. Use SHAP to explain baseline and post-processed models globally  
5. Use LIME to explain individual predictions from both models  
6. Compare fairness metrics (statistical parity difference) and explanation accuracy  

LIVE_CONTEXT_ADD: Synthetic loan data parameters and fairness experiment plan documented in memory/research/ai-ethics.md. Ready to execute once Rob arrives to lift cold-start gate.