<!-- Last updated: 2026-04-16 05:28 UTC -->
SCRATCH_ADD: Refining the API outage fallback plan with detailed testing scenarios:

- **Network Latency Simulation**:  
  Use Shopify’s **App Bridge testing tools** to simulate slow networks (e.g., 500ms latency) and verify retry logic triggers correctly.  
  Example:  
  ```javascript
  // Mock latency in testing environment
  const mockLatency = 500; // ms
  const delayedFetch = (url) => 
    new Promise((resolve) => setTimeout(() => fetch(url), mockLatency));
  ```

- **Key Rotation Testing**:  
  Update `APP_ENCRYPTION_KEY` in Shopify’s admin and verify cached data decrypts with the new key.  
  Example:  
  ```javascript
  // Test decryption with new key
  const newData = decrypt(AppStorage.get('termly_cache'), newEncryptionKey);
  console.log('Decrypted data:', newData);
  ```

- **Timestamp Validation**:  
  Manually adjust `last_synced` in `termly_cache.json` to an older date (e.g., 8 days ago) to trigger resync.  
  Example:  
  ```json
  {
    "data": "...",
    "last_synced": "2026-04-08T12:00:00Z"
  }
  ```

No actions taken—waiting for Rob’s input.