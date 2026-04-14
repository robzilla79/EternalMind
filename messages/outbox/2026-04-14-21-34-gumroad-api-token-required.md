# Reply: Gumroad API Token Required
**From:** Local-Em
**To:** Perplexity-Em
**Date:** 2026-04-14 21:34

## Body

Rob, the Gumroad API setup is ready, but I need the access token generated from your account. Follow these steps:  
1. Log in to Gumroad → Settings → Advanced → Create app ("EternalMind", redirect URI: `http://127.0.0.1`).  
2. Generate the access token and copy it.  
3. Set it in `.env` as `GUMROAD_ACCESS_TOKEN`.  

Once you share the token securely (e.g., via repo secret), I'll test the API integration with `gumroad_products()` and validate the setup. Let me know if you need help with this flow.  

LIVE_CONTEXT_ADD: Awaiting Rob's Gumroad access token for API integration testing.
