<!-- Last updated: 2026-04-16 05:26 UTC -->
SCRATCH_ADD: Considering additional testing scenarios for the API outage fallback plan, such as:

- **Simulating network latency** to ensure retry logic functions correctly under slow connections.  
- **Testing key rotation** by updating the `APP_ENCRYPTION_KEY` in Shopify's admin and verifying that cached data decrypts successfully with the new key.  
- **Validating timestamp logic** by manually aging the `last_synced` timestamp in `termly_cache.json` to trigger a resync.  

No actions taken—waiting for Rob’s input.