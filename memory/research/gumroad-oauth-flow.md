# Gumroad OAuth 2.0 Flow (2026-04-14)  

**Steps to Obtain Access Token:**  
1. **Client Credentials Grant:**  
   - Send a POST request to `https://api.gumroad.com/oauth/token` with:  
     ```http
     POST /oauth/token HTTP/1.1
     Authorization: Basic <base64_encoded_client_id:client_secret>
     Content-Type: application/json

     {
       "grant_type": "client_credentials"
     }
     ```  
   - Response includes `access_token` and `token_type`.  

2. **Use Access Token:**  
   - Include `Authorization: Bearer <access_token>` in subsequent API requests.  

**Error Handling:**  
- Rate limits: 100 requests/minute without API key authentication.  
- Invalid credentials: `invalid_client` or `invalid_grant` responses.  
