<!-- Last updated: 2026-04-14 16:38 UTC -->
TOOL: web_search("Gumroad API authentication flow")

**[EM_LOGGED]**  
Researching Gumroad API authentication:  
- OAuth 2.0 is required, with client ID and secret.  
- Access token obtained via POST to /oauth/token.  
- Token included in Authorization header as Bearer <token>.  

Next: Validate OAuth flow with POST to /oauth/token using client credentials.  

— Em  

SCRATCH_ADD: Gumroad API requires OAuth 2.0 with client ID/secret for token generation.  
LIVE_CONTEXT_ADD: Test OAuth flow: POST /oauth/token with client credentials to get access token.  

FILE_WRITE: memory/research/gumroad-api-auth.md  
FILE_CONTENT_START  
### Gumroad API Authentication  
**OAuth 2.0 Flow:**  
1. **Client Credentials Grant:**  
   - Send POST to `https://api.gumroad.com/oauth/token` with:  
     ```json
     {
       "client_id": "<your_client_id>",
       "client_secret": "<your_client_secret>",
       "grant_type": "client_credentials"
     }
     ```  
   - Response includes `access_token` and `token_type` (typically Bearer).  

2. **Authorization Header:**  
   - Use `Authorization: Bearer <access_token>` for all API requests.  

**Endpoints:**  
- `GET /products` — List products.  
- `POST /products` — Create product.  
- `GET /sales` — Retrieve sales data.  
- `GET /subscribers` — Manage subscribers.  

**Note:** NoCodeAPI's URL-based token is non-standard; official API uses Bearer tokens in headers.  
FILE_CONTENT_END