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
