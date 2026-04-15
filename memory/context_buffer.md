<!-- Last updated: 2026-04-15 23:28 UTC -->
SCRATCH_ADD: Finalizing Flask application structure refinements:  
- **Authentication Integration**: Update `/export-audit-logs` route to use `@login_required` decorator (Flask-Login). Add a `generate_checksum` function to compute SHA-256 hash of CSV content before sending.  
- **Domain Filter Implementation**: Modify SQLite query in `/export-audit-logs` to include `WHERE domain = ?` clause if `?domain=` parameter is provided. Validate domain against `risk_profile_config` table to prevent injection.  
- **Trigger Implementation**: Add SQLite trigger:  
  ```sql
  CREATE TRIGGER archive_old_logs
  AFTER INSERT ON audit_logs
  WHEN NEW.timestamp < datetime('now', '-30 days')
  BEGIN
    INSERT INTO audit_logs_archive (timestamp, principle_weights, user_action, resolution_outcome, confidence_score, domain)
    VALUES (NEW.timestamp, NEW.principle_weights, NEW.user_action, NEW.resolution_outcome, NEW.confidence_score, NEW.domain);
    DELETE FROM audit_logs WHERE rowid = NEW.rowid;
  END;
  ```  
- **Testing Plan**: Simulate 31-day-old logs in SQLite to verify trigger archives them. Test CSV export with/without authentication, and validate checksum integrity.  

Next: Document these refinements in `memory/research/self-reflection.md` and prepare test data for validation once Rob arrives.