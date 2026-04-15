# PHI Validation Clarification and Sensitivity/Specificity Tracking  

**Prevalence Assumptions:**  
- Synthetic datasets simulate **algorithmic robustness**, not clinical prevalence.  
- No baseline prevalence rates baked into data (avoids conflating with clinical thresholds).  

**Sensitivity/Specificity Tracking Added:**  
- For each synthetic dataset, calculate:  
  - Sensitivity = TP / (TP + FN)  
  - Specificity = TN / (TN + FP)  
  - Example:  
    ```python  
    from sklearn.metrics import confusion_matrix  
    y_true = [...]  # Ground truth labels  
    y_pred = [...]  # Model predictions  
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()  
    sensitivity = tp / (tp + fn)  
    specificity = tn / (tn + fp)  
    ```  

**Clinical Threshold Benchmarking:**  
- Compare results to NCBI AUC 0.70 benchmark[1] for non-clinical applicability.  
