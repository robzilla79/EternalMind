<!-- Last updated: 2026-04-16 05:18 UTC -->
SCRATCH_ADD: Adding **cache validation** and **security considerations** to the API outage fallback plan:

- **Cache Validation**:  
  - Add a `last_synced` timestamp to `termly_cache.json` to ensure cached content isn't stale.  
  - Example:  
    ```json
    {
      "data": "...",
      "last_synced": "2026-04-16T12:00:00Z"
    }
    ```  
  - If `last_synced` is older than 7 days, force a resync during the next background job.  

- **Security Enhancements**:  
  - Encrypt cached legal text using Shopify’s **App Bridge encryption** before storing in `app_storage`.  
  - Example:  
    ```javascript
    const encryptedData = encrypt(JSON.stringify(data), 'YOUR_ENCRYPTION_KEY');
    AppStorage.set('termly_cache', encryptedData);
    ```  
  - Decrypt data at render time using the same key.  

- **Manual Cache Refresh**:  
  - Add a **"Refresh Legal Text"** button in the Shopify app settings to trigger an immediate sync (bypassing the 24-hour interval).  

- **Testing Checklist for Rob**:  
  1. Test API outage by disabling Termly’s API in staging.  
  2. Verify fallback to cached content (check `termly_cache.json`).  
  3. Test manual refresh button in app settings.  
  4. Ensure encrypted data is decrypted correctly in `/privacy-policy.html`.  

No actions taken—waiting for Rob’s input.