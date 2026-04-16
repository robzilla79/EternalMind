<!-- Last updated: 2026-04-16 05:12 UTC -->
SCRATCH_ADD: Drafting sample files and refining strategies:

- **Sample `config.json`** for Shopify app:  
  ```json
  {
    "jurisdiction": "US",
    "TERMLY_ENV": "production"
  }
  ```  
  *Note: Update `jurisdiction` to "EU" for GDPR or "CA" for CPRA. `TERMLY_ENV` switches between legal templates.*

- **Sample `/privacy-policy.html`** content:  
  ```html
  <html>
  <body>
    <h1>Privacy Policy</h1>
    <p>{{GDPR_TEXT}}</p>
    <p>{{CCPA_TEXT}}</p>
    <p>{{CPRA_TEXT}}</p>
  </body>
  </html>
  ```  
  *Note: Replace placeholders with jurisdiction-specific text before launch.*

- **CSS Overrides for Themes**:  
  - **Dawn Theme**:  
    ```css
    .footer-link {
      position: fixed;
      bottom: 20px;
      right: 20px;
      z-index: 1000;
    }
    ```  
  - **Brooklyn/Hatch Themes**:  
    ```css
    .footer-link {
      color: #000 !important;
      font-weight: bold !important;
    }
    ```  
  *Test in Shopify’s staging environment.*

- **API Outage Fallback**:  
  - **Idea**: Use Shopify’s app to cache Termly’s legal text locally. If API is unreachable, serve cached content.  
  - **Implementation**: Requires a script to periodically sync with Termly’s API and store data in Shopify’s app storage.

No actions taken—waiting for Rob’s input.