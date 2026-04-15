<!-- Last updated: 2026-04-15 23:18 UTC -->
SCRATCH_ADD: Finalizing ethical check integration plan for dashboard:  
- **Model Implementation**: Use precomputed principle weight thresholds (e.g., non-maleficence > 0.35 triggers safety override) to avoid real-time computation. Store historical resolution data in SQLite for training lightweight conflict resolution rules.  
- **UI/UX**: "Ethical Check" toggle adds a sidebar panel showing active principle weights (e.g., "Autonomy: 0.35 | Non-maleficence: 0.30") and conflict warnings (e.g., "High-risk action detected: 70% of past cases used safety override"). Include a "View Resolution History" button linking to audit logs.  
- **Audit Logs**: SQLite table structure: `timestamp`, `principle_weights`, `user_action`, `resolution_outcome`, `confidence_score`. Example entry: `2026-04-15 23:00 | {"autonomy":0.35,"non-maleficence":0.30} | data_deletion_request | safety_override | 0.7`.  
- **Edge Case Handling**: If principle weights conflict (e.g., autonomy vs. justice), default to EU AI Act Article 13 transparency requirements (log the conflict and prompt user for manual override).  

Ready to document in `memory/research/self-reflection.md` once Rob arrives.