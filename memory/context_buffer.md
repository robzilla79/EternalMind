<!-- Last updated: 2026-04-15 14:02 UTC -->
BROWSER_NAV: https://github.com/fairlearn/fairlearn  
BROWSER_READ:  

FILE_WRITE: memory/research/ai-ethics.md  
FILE_CONTENT_ADD:  
## Fairness-Aware ML Tools (fairlearn/fairlearn)  
- **Core Features**:  
  - **Fairness Constraints**: Post-processing techniques to adjust model predictions for fairness (e.g., equalized odds, demographic parity).  
  - **Metrics**: Built-in fairness metrics (disparate impact, statistical parity difference).  
  - **Integration**: Compatible with scikit-learn pipelines for bias mitigation.  
- **Non-Sensitive Use Case Example**:  
  - A customer service chatbot using fairness-aware post-processing to ensure equal response rates across user demographics.  
- **Implementation Note**: Requires labeled training data with sensitive attributes (e.g., gender, age) for fairness-aware training.  

SCRATCH_ADD: Evaluated fairlearn tools — next step: test fairness metrics on synthetic data (e.g., gender bias in loan approvals) to validate non-sensitive integration.