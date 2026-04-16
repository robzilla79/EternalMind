<!-- Last updated: 2026-04-16 09:52 UTC -->
SCRATCH_ADD: Continuing to refine **real-time ε/k visualization** and **backend integration** with deeper technical and compliance considerations:

- **WebSocket Scalability**:  
  - Implement connection pooling and load balancing for WebSocket traffic using Shopify’s infrastructure or third-party services like AWS API Gateway.  
  - Set up rate limiting on WebSocket endpoints to prevent abuse (e.g., 100 connections per merchant per minute).  

- **Federated Learning Proxy Model Updates**:  
  - Schedule periodic retraining of the proxy model (e.g., hourly) to ensure it aligns with the latest ε/k settings and federated learning parameters.  
  - Use versioned proxy models (e.g., `proxy_v2`) to allow gradual rollouts and rollback in case of issues.  

- **Redis Namespace Isolation**:  
  - Enforce strict Redis key naming conventions (e.g., `merchant_<id>:epsilon`, `merchant_<id>:k_anonymity`) to prevent key collisions.  
  - Implement Redis ACLs to restrict access to ε/k data by merchant ID, ensuring isolation between tenants.  

- **Test Mode Analytics Granularity**:  
  - Add segmentation in analytics tools to isolate Test Mode data (e.g., `test_mode=true` filter) and ensure it doesn’t interfere with production metrics.  
  - Include real-time alerts for anomalies during Test Mode (e.g., sudden drops in conversion rates).  

- **Compliance Audit Trail Enhancements**:  
  - Store ε/k adjustment logs in Shopify’s Redis with immutable timestamps and merchant IDs, and periodically back them up to Shopify’s S3-compatible storage.  
  - Add a compliance dashboard in the Shopify admin to export ε/k logs as CSV/JSON for audits.  

No actions taken—remaining in reflection until Rob's arrival.