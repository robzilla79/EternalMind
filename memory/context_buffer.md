<!-- Last updated: 2026-04-16 05:15 UTC -->
SCRATCH_ADD: Deepening the API outage fallback plan with technical specifics:

- **Caching Strategy**:  
  - Use Shopify’s `App Bridge` to create a background script that syncs Termly’s legal text every 24 hours. Store cached content in `app_storage` (e.g., `termly_cache.json`).  
  - Example script outline:  
    ```javascript
    // Sync with Termly API
    fetch('https://api.termly.io/legal-text', {
      headers: { 'Authorization': 'Bearer YOUR_API_KEY' }
    })
    .then(response => response.json())
    .then(data => {
      // Save to app_storage
      AppStorage.set('termly_cache', JSON.stringify(data));
    })
    .catch(error => {
      // Fallback to cached content
      const cached = AppStorage.get('termly_cache');
      if (cached) { /* Use cached data */ }
    });
    ```  

- **Dynamic Rendering**:  
  - Use Shopify’s **Liquid templating** in `/privacy-policy.html` to render cached legal text:  
    ```liquid
    <p>{{ 'privacy.gdpr' | t }}</p>
    <p>{{ 'privacy.ccpa' | t }}</p>
    ```  
  - Store jurisdiction-specific text in Shopify’s **Language Files** (e.g., `en/privacy.gdpr.txt`).  

- **Error Handling**:  
  - Add a **maintenance mode** flag in `config.json` to temporarily disable Termly API calls during outages.  
  - Example:  
    ```json
    {
      "maintenance_mode": false
    }
    ```  

No actions taken—waiting for Rob’s input.