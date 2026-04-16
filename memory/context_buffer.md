<!-- Last updated: 2026-04-16 09:57 UTC -->
SCRATCH_ADD: Continuing to refine **real-time ε/k visualization** and **backend integration** with deeper technical and compliance considerations:

- **WebSocket Security Reinforcements**:  
  - Implement **mutual TLS (mTLS)** for WebSocket connections to ensure both client and server authenticate each other, preventing man-in-the-middle attacks.  
  - Use **HSTS (HTTP Strict Transport Security)** headers to enforce HTTPS for all WebSocket traffic, reducing the risk of downgrade attacks.  

- **Federated Learning Model Isolation**:  
  - Deploy proxy models in **isolated Kubernetes namespaces** per merchant to prevent cross-tenant data leakage, even during canary releases.  
  - Use **service meshes** (e.g., Istio) to enforce strict network policies between federated learning components and external services.  

- **Redis Data Encryption**:  
  - Enable **at-rest encryption** for Redis backups stored in S3, using AWS KMS or Shopify’s native encryption tools.  
  - Implement **encryption-in-transit** for Redis backups using AES-256-GCM, ensuring data integrity and confidentiality during transfers.  

- **Test Mode Limitations Clarification**:  
  - Add **disclaimer banners** in Test Mode to explicitly state that results are not representative of live performance (e.g., "Test Mode data is synthetic; live performance may vary").  
  - Include **disabling Test Mode** as a prerequisite for merchants to access production data, preventing accidental reliance on incomplete metrics.  

- **Compliance Dashboard Automation**:  
  - Integrate **real-time compliance alerts** (e.g., "ε/k threshold exceeded for merchant X") via Shopify’s native notification system or email.  
  - Add **automated remediation workflows** (e.g., suggesting ε/k adjustments if privacy metrics fall below thresholds).  

No actions taken—remaining in reflection until Rob's arrival.