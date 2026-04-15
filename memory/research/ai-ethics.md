## Synthetic Loan Data Experiment (Paused for Cold-Start Gate)  
**Status**: On hold due to active cold-start gate (Rob not present).  
**Preparation Completed**:  
- Experiment parameters finalized (bias injection: race='B', income<50k; tools: SDV 0.19.1, AIF360 0.5.1, MLflow 2.1.0).  
- Safeguards documented per Cloud-Em: explicit bias logging, human oversight, equity checks.  
- Research notes updated with UNESCO policy actions[2][6] and fairness accountability frameworks[1][4].  

**Next Steps**:  
1. Wait for Rob's arrival to lift cold-start gate.  
2. Generate synthetic data via SDV/CTGAN (requires Rob's approval).  
3. Apply AIF360 mitigation and evaluate with SHAP/LIME.  
4. Log results to MLflow and document in ai-ethics.md.  
