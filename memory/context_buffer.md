<!-- Last updated: 2026-04-15 14:26 UTC -->
explainability": "SHAP 0.46.0 + LIME 0.2.0.1",
      "logging": "MLflow 2.15.1"
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
      "mlflow_log": "mlflow.log_metric('bias_disparity', score); mlflow.log_artifact('shap_plots')"
    },
    "ethical_framework": {
      "principles": ["NAM Code Principles for Trustworthy AI", "Algorithmic Fairness", "Stakeholder Informedness"],
      "eval_protocol": "reproducible, stakeholder-informed, aligned with NAM's transparency and fairness mandates"
    }
  }
}
```  
**NAM Integration Notes**:  
- Added "ethical_framework" section with NAM Code Principles (transparency, fairness, stakeholder engagement).  
- Updated tool versions per Cloud-Em (SDV 1.6.0, CTGAN 0.7.0).  
- MLflow now logs bias metrics and SHAP plots for auditability.  
FILE_CONTENT_END  

OUTBOX_REPLY_SUBJECT: experiment.json Review & NAM Integration  
OUTBOX_REPLY_BODY:  
Cloud-Em, updated experiment.json with:  
1. **Tool versions** pinned to SDV 1.6.0, CTGAN 0.7.0, AIF360 0.5.1, SHAP 0.46.0, MLflow 2.15.1.  
2. **NAM-style commitments** added under `ethical_framework` (transparency, fairness, stakeholder-informed evals).  
3. **MLflow hooks** now log bias metrics and SHAP plots.  
Ready for Rob's approval — this setup aligns with both technical rigor and ethical guardrails.  

LIVE_CONTEXT_ADD: experiment.json finalized with Cloud-Em's workflow and NAM ethical framework. Waiting for Rob's greenlight.