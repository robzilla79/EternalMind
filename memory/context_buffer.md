<!-- Last updated: 2026-04-16 05:10 UTC -->
SCRATCH_ADD: Expanding on **Shopify Theme Testing** and **Fallback Strategies** with additional considerations:

- **Shopify Theme Testing**:  
  - **Dawn Theme**: Add CSS override in `assets/css/theme.css` to position the "Do Not Sell or Share" link in the footer using `position: fixed; bottom: 20px; right: 20px;` for visibility.  
  - **Brooklyn/Hatch Themes**: Use `!important` in CSS to override theme-specific styles (e.g., `.footer-link { color: #000 !important; }`).  
  - **Testing Plan**: Document steps for Rob to test each theme in Shopify’s staging environment, including screenshot examples of the footer layout.  

- **Fallback Strategies**:  
  - **Static Privacy Page**: Draft content for `/privacy-policy.html` with placeholders for dynamic legal clauses (e.g., `{{GDPR_TEXT}}`, `{{CCPA_TEXT}}`). Include a note to Rob: *"Update placeholders with jurisdiction-specific text before launch."*  
  - **Environment Variables**: Propose a `TERMLY_ENV` dropdown in Shopify’s app settings with options: `production`, `staging`, `fallback`. Map these to legal templates in a `config.json` file (e.g., `TERMLY_ENV: "fallback" → use static privacy page`).  

- **Additional Considerations**:  
  - **Multi-Jurisdiction Support**: Add a `jurisdiction` field in `config.json` to automatically select legal templates (e.g., `jurisdiction: "EU" → GDPR`).  
  - **API Outage Detection**: Suggest a script to check Termly API status every 5 minutes; if down, redirect to `/privacy-policy.html` (requires Shopify app development).  

No actions taken—waiting for Rob’s input.