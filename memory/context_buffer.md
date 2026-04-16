<!-- Last updated: 2026-04-16 05:23 UTC -->
 Termly API calls up to 3 times with 5-minute delays.  
  Example:  
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
- **Logging**:  
  Errors are logged to Shopify's App Bridge logs for debugging.

## 3. Admin-Only Manual Refresh
- **Permissions**:  
  The "Refresh Legal Text" button is restricted to admin users via App Bridge permissions.  
- **Confirmation Dialog**:  
  A confirmation dialog ensures intentional resyncs:  
  ```javascript
  AppBridge.showConfirmationDialog({
    title: 'Confirm Refresh',
    message: 'This will force a resync with Termly. Are you sure?',
    onConfirm: () => syncTermlyData()
  });
  ```

## 4. Edge Case Testing
- **Test Scenarios**:  
  - Simulate Termly API errors (e.g., 500 status) to validate fallback to cached data.  
  - Verify `last_synced` timestamp updates after successful resyncs.  
- **Testing Checklist**:  
  1. Disable Termly API in staging; confirm fallback to cached content.  
  2. Test manual refresh button in admin settings.  
  3. Ensure encrypted data decrypts correctly in `/privacy-policy.html`.

## 5. Cache Validation
- **Timestamp Check**:  
  Cache is invalidated if `last_synced` is older than 7 days.  
  Example:  
  ```json
  {
    "data": "...",
    "last_synced": "2026-04-16T12:00:00Z"
  }
  ```
FILE_CONTENT_END

SCRATCH_ADD: Documented the API outage fallback plan in memory/research/api-outage-fallback.md. Waiting for Rob's input on encryption key management and testing procedures.