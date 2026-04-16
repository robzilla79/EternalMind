<!-- Last updated: 2026-04-16 05:31 UTC -->
SCRATCH_ADD: Adding **user experience considerations** to the API outage fallback plan:

- **Fallback UI Notification**:  
  Display a subtle banner to users during fallback mode:  
  *"Currently using cached legal content. Please check back later for updates."*  
  This avoids confusion while maintaining transparency.

- **Admin Dashboard Alerts**:  
  Add a red alert in the Shopify admin if fallback mode is active, with a call-to-action to "Check Termly API status" and "Force resync if needed."

- **Edge Case: No Cache Available**:  
  If `termly_cache.json` is missing or corrupted, show a fallback message:  
  *"Unable to load legal content. Please contact support."*  
  This prevents blank pages and ensures compliance visibility.

No actions taken—waiting for Rob’s input.