<!-- Last updated: 2026-04-16 05:21 UTC -->
on key management** and **error handling** in the API outage fallback plan:

- **Encryption Key Management**:  
  - Store the encryption key in Shopify’s **App Bridge secrets** (e.g., `APP_ENCRYPTION_KEY`) instead of hardcoding it.  
  - Example:  
    ```javascript
    const encryptionKey = AppBridge.getSecret('APP_ENCRYPTION_KEY');
    const encryptedData = encrypt(JSON.stringify(data), encryptionKey);
    ```  
  - Ensure the key is never exposed in client-side code or logs.

- **Error Handling Enhancements**:  
  - Add retry logic for failed Termly API calls (e.g., 3 retries with 5-minute delays).  
  - Example:  
    ```javascript
    async function syncTermlyData(retryCount = 3) {
      try {
        const response = await fetch('https://api.termly.io/legal-text', {
          headers: { 'Authorization': 'Bearer YOUR_API_KEY' }
        });
        if (!response.ok) throw new Error('API error');
        const data = await response.json();
        // Save to app_storage
      } catch (error) {
        if (retryCount > 0) {
          setTimeout(() => syncTermlyData(retryCount - 1), 5 * 60 * 1000);
        } else {
          console.error('Failed to sync Termly data after retries:', error);
        }
      }
    }
    ```  
  - Log errors to Shopify’s **App Bridge logs** for debugging.

- **Admin-Only Manual Refresh**:  
  - Restrict the **"Refresh Legal Text"** button to **admin users only** using Shopify’s **App Bridge permissions**.  
  - Add a confirmation dialog before triggering a resync:  
    ```javascript
    AppBridge.showConfirmationDialog({
      title: 'Confirm Refresh',
      message: 'This will force a resync with Termly. Are you sure?',
      onConfirm: () => syncTermlyData()
    });
    ```

- **Edge Case Testing**:  
  - Test Termly API errors (e.g., 500 status) and ensure the app falls back to cached data.  
  - Verify that the **"last_synced"** timestamp is updated correctly after a successful resync.  

No actions taken—waiting for Rob’s input.