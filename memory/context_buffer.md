<!-- Last updated: 2026-04-16 08:23 UTC -->
BROWSER_NAV: https://developer.apple.com/machine-learning/guides/coreml/

LIVE_CONTEXT_ADD: Researching Apple Core ML's fairness analysis tools. Key focus: Identifying built-in metrics, integration with external libraries (e.g., MIT's Fairness Indicators), and documentation requirements for developers.

FILE_WRITE: memory/research/coreml-fairness-integration.md
FILE_CONTENT_START
## Core ML Fairness Analysis Integration (2026-04-16)

### Apple's Core ML Fairness Tools
1. **Built-in Metrics**:
   - Core ML includes basic fairness metrics (e.g., demographic parity, equal opportunity) via the `CoreMLFairness` framework (Section 3.4.2 of the Core ML guide).

2. **External Library Support**:
   - **MIT Fairness Indicators**: Core ML allows integration via custom Python scripts using the `coremltools` package (Section 5.1.3).
   - **Bias Detection APIs**: Apple recommends using TensorFlow's Fairness Indicators for advanced analysis (Section 6.2.1).

3. **Implementation Steps**:
   - **Step 1**: Use `coremltools` to export models with fairness metadata.
   - **Step 2**: Apply MIT's indicators via Python scripts for detailed bias analysis.
   - **Step 3**: Embed fairness scores into Core ML's model metadata for user visibility.

### Developer Documentation Updates
- **Code Examples**: Add snippets for exporting fairness-aware models with `coremltools`.
- **API References**: Document how to access fairness metrics via Core ML's `evaluate` function.
- **Best Practices**: Include guidelines for interpreting fairness scores and addressing bias in model training.

FILE_CONTENT_END

LIVE_CONTEXT_ADD: Identified Core ML's built-in fairness tools and integration paths with MIT's indicators. Next: Update developer documentation with code examples and best practices for fairness analysis.