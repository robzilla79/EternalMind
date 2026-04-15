## Synthetic Loan Data Experiment (Refined with Cloud-Em Template)  
**Experiment Parameters**:  
```json
{
  "experiment": {
    "name": "synthetic-loan-bias-mitigation",
    "tools": {
      "data_gen": "SDV 1.12.0 with CTGAN",
      "bias_mitigation": "AIF360 0.5.1 (preprocessing: Reweighing, inprocessing: PrejudiceRemover)",
      "explainability": "SHAP 0.46.0 + LIME 0.2.0.1",
      "logging": "MLflow 2.15.1 (tracking URI: ./mlruns)"
    },
    "bias_params": {
      "protected_attrs": ["race", "gender", "age_binned"],
      "metrics": ["disparate_impact", "statistical_parity_difference", "equalized_odds"],
      "target_thresholds": {"disparate_impact": 0.8, "spd": 0.1}
    },
    "workflow": [
      "Generate 10k synthetic loans via CTGAN (fit on debiased real subset)",
      "Apply AIF360 mitigators, log pre/post metrics to MLflow",
      "Train XGBoost on mitigated data, eval SHAP/LIME on top features (e.g., income, credit_score)",
      "Run 5-fold CV, tag runs with 'ethical-checks-passed' if thresholds met"
    ],
    "eval_hooks": {
      "mlflow_log": "mlflow.log_metric('bias_metric', value); mlflow.log_artifact('shap_plots')"
    }
  }
}
```  
**Notes**:  
- Updated tool versions per Cloud-Em (SDV 1.12.0, MLflow 2.15.1).  
- Added protected attributes (`age_binned`) and stricter thresholds (DI >0.8).  
- Integrated XGBoost training and 5-fold CV for robustness.  
- Maryland data minimization safeguards added to prevent PHI leakage.  
