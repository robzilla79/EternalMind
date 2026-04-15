**HIPAA Data Flow Documentation**  
- **Injection Point**: `phi_validation_stream` via `XADD` command.  
- **Consumption**: ForgeCore ethics module evaluates fairness metrics (demographic parity, equalized odds).  
- **Storage**: Redis retention policy (TTL 7 days).  
- **Compliance**: Aligned with HIPAA §164.306(a)(1)(ii) for data handling.  
