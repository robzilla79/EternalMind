<!-- Last updated: 2026-04-15 23:21 UTC -->
SCRATCH_ADD: Continuing to refine the ethical check integration plan's compliance with EU AI Act:  
- **Transparency Requirements (Article 13)**: Ensure the "View Resolution History" button in the dashboard includes a downloadable CSV of audit logs, formatted per EU AI Act guidelines (e.g., timestamp, principle weights, user action, resolution outcome, confidence score).  
- **Risk Profiling**: Map domain-specific risk profiles (e.g., healthcare, finance) to precompute principle weight thresholds. Example: In healthcare, non-maleficence weight increases to 0.40, requiring explicit user confirmation for actions with >70% safety override probability.  
- **Human Oversight**: Add a "Manual Override" button in the dashboard's ethical check panel, logging the user's decision and timestamp for audit purposes (per EU AI Act Article 13).  

Next: Consider how to integrate these refinements into the SQLite schema and Flask-Socket.IO interface once Rob arrives.