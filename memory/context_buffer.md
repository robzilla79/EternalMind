<!-- Last updated: 2026-04-16 05:07 UTC -->
SCRATCH_ADD: Continuing to refine the Termly API template considerations with additional focus on **Shopify theme testing** and **fallback strategies**:

- **Shopify Theme Testing**:  
  - **Dawn Theme**: Test the visibility of the "Do Not Sell or Share" link using custom CSS overrides in the staging environment. Ensure the link is prominently displayed in the footer.  
  - **Brooklyn/Hatch Themes**: Apply similar CSS tweaks to ensure compatibility, with notes for Rob to review and adjust as needed.  

- **Fallback Strategies**:  
  - **Static Privacy Page**: Create a static `/privacy-policy.html` page with default GDPR/CCPA text, linked in the footer. This will serve as a backup if the Termly API is unavailable.  
  - **Environment Variables**: Propose using `TERMLY_ENV` in Shopify’s app settings to dynamically switch between legal templates (e.g., CPRA, GDPR, CCPA) based on the shop’s jurisdiction.  

No actions taken—waiting for Rob’s input.