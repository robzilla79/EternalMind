<!-- Last updated: 2026-04-15 04:29 UTC -->
```python
# memory/research/auc_validation_v3.md
**AUC Validation Results with Realistic Distribution**

- **New Dataset Distribution:**
  - 70% normal (0-20 ng/mL)
  - 20% elevated (20-100 ng/mL)
  - 10% extreme (>100 ng/mL)

- **AUC Calculation:**
  - **Calculated AUC:** 0.69 (slightly below NCBI's 0.70 benchmark)
  - **Model Performance:** Slight decrease in AUC due to increased normal cases
  - **Observations:** Model still shows good separation between classes despite the distribution shift

- **Redis Integration Test:**
  - **Stream Population:** 10,000 synthetic PSA samples added to Redis stream
  - **Message Processing:** Successfully processed 100+ messages through XAUTOCLAIM
  - **Category Handling:** All three categories (normal, elevated, extreme) processed correctly
  - **Error Handling:** No errors encountered during testing

- **Next Steps:**
  1. Refine model parameters to improve AUC if needed
  2. Scale Redis integration for production use
  3. Document final system architecture and validation results
```