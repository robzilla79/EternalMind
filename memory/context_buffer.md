<!-- Last updated: 2026-04-15 23:23 UTC -->
SCRATCH_ADD: Designing the SQLite schema and Flask-Socket.IO integration for ethical checks:  
- **SQLite Schema Enhancements**:  
  - Add a `domain` field to the audit logs table to track risk profiles (e.g., "healthcare", "finance").  
  - Example row: `2026-04-15 23:00 | {"autonomy":0.35,"non-maleficence":0.40} | data_deletion_request | safety_override | 0.7 | healthcare`.  
  - Include a `risk_profile_config` table mapping domains to precomputed principle weights (e.g., `healthcare: {"non-maleficence": 0.40}`).  

- **Flask-Socket.IO Integration**:  
  - **Dynamic Principle Weights**: When a user selects a domain, emit a `DOMAIN_SELECTED` event to update the sidebar panel with domain-specific weights (e.g., "Non-maleficence: 0.40").  
  - **Manual Override Handling**: When the "Manual Override" button is clicked, emit a `MANUAL_OVERRIDE` event, log the action with the current timestamp and principle weights into SQLite, and notify the user via a Socket.IO alert (e.g., "Override logged: 2026-04-15 23:05").  

- **CSV Export Implementation**:  
  - Create a Flask route (`/export-audit-logs`) that queries the audit logs table, formats the data as CSV (with headers: `timestamp,principle_weights,user_action,resolution_outcome,confidence_score,domain`), and sends it as a downloadable file.  

Next: Document this plan in `memory/research/self-reflection.md` once Rob arrives.