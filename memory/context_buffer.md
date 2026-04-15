<!-- Last updated: 2026-04-15 23:26 UTC -->
SCRATCH_ADD: Continuing to refine the CSV export implementation:  
- **Export Route Security**: Add a Flask route `/export-audit-logs` that requires user authentication (via Flask-Login) to prevent unauthorized access. The CSV file should include a checksum hash in the headers for integrity verification (e.g., `checksum:sha256-abc123...`).  
- **Domain-Specific Export Filters**: Allow users to filter audit logs by domain (e.g., `?domain=healthcare`) in the CSV export URL. Example: `/export-audit-logs?domain=finance`.  
- **Audit Log Retention**: Implement a SQLite trigger to automatically archive audit logs older than 30 days into a `audit_logs_archive` table, ensuring compliance with data minimization principles (EU AI Act Article 24).  

Next: Consider how to integrate these refinements into the Flask application structure once Rob arrives.