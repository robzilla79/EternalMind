<!-- Last updated: 2026-04-16 12:37 UTC -->
SCRATCH_ADD: Continuing internal refinement of ε/k system documentation with focus on **real-time legal integration** and **merchant onboarding flow**. Additional considerations:  
- **Cache Expiry Strategy**: Implement time-to-live (TTL) for cached EUR-Lex API responses (e.g., 24-hour refresh window) to balance freshness with rate-limiting efficiency.  
- **Consent Granularity**: Allow merchants to opt-in/out of specific legal domains (e.g., "GDPR only" vs. "all EU laws") rather than a binary toggle.  
- **Regional Profile Conflict Resolution**: Define rules for overlapping regulations (e.g., prioritize stricter thresholds if a merchant operates in both EU and APAC).  
- **Test Case Prioritization**: Focus on high-impact scenarios first (e.g., sudden CCPA expansion, GDPR fine adjustments) to validate core system resilience.  
- **Simulator Educational Layer**: Include tooltips in the Privacy Impact Simulator explaining terms like "ε/k trade-off" and "data utility vs. privacy risk."  

No actions taken—remaining in reflection until Rob's arrival.