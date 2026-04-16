<!-- Last updated: 2026-04-16 07:36 UTC -->
SCRATCH_ADD: Preparing for Rob’s review by refining the federated learning plan with additional focus on **legal language precision**, **bias audit tool validation**, and **cloud storage cost analysis**. Key refinements:

- **Legal Language**:  
  - Add explicit opt-out mechanisms for GDPR/CPRA compliance (e.g., *"You may opt out of data use for personalization at any time via your account settings"*).  
  - Include data retention clauses: *"User data will be deleted within 30 days of opt-out."*  

- **Bias Audit Tools**:  
  - Validate IBM AI Fairness 360’s compatibility with federated learning workflows.  
  - Explore alternative tools like Fairlearn (Microsoft) for additional fairness metrics.  

- **Cloud Storage**:  
  - Compare AWS S3 vs. Google Cloud Storage for federated learning:  
    - **AWS**: $0.023/GB/month (S3 Standard).  
    - **GCP**: $0.027/GB/month (Regional Storage), but with potential cost savings via reserved instances.  
  - Document findings in `memory/research/cloud-costs.md`.  

No actions taken—waiting for Rob’s input.