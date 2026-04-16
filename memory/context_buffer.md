<!-- Last updated: 2026-04-16 05:04 UTC -->
SCRATCH_ADD: Deepening Termly API template considerations:  
- **Dynamic Jurisdiction Handling**: Implement a fallback to default GDPR/CCPA text if CPRA data is incomplete, with a note to Rob for manual review.  
- **Shopify Theme Compatibility**: Ensure the "Do Not Sell or Share" link is visible in Dawn, Brooklyn, and Hatch themes via CSS overrides (to be tested in staging).  
- **Environment Variables**: Propose using `TERMLY_ENV` in Shopify’s app settings to switch between legal templates, with a placeholder for Rob to configure.  
- **Fallback Static Page**: Plan a static HTML page (e.g., `/privacy-policy.html`) with default legal text for Termly API outages, linked in the footer.  

No actions taken—waiting for Rob’s input.