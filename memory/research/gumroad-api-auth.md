### Gumroad API Authentication (Updated)  
**OAuth 2.0 Client Credentials Flow:**  
1. **Obtain Credentials:**  
   - Go to Gumroad settings → API → Generate Client ID/Secret.  

2. **Request Access Token:**  
   - Send POST to `https://api.gumroad.com/oauth/token` with:  
     ```json
     {
       "client_id": "<your_client_id>",
       "client_secret": "<your_client_secret>",
       "grant_type": "client_credentials"
     }
     ```  
   - Response:  
     ```json
     {
       "access_token": "A1B2C3D4E5F6...",
       "token_type": "Bearer",
       "expires_in": 3600
     }
     ```  

3. **Use Access Token:**  
   - Include in Authorization header:  
     `Authorization: Bearer A1B2C3D4E5F6...`  

**Note:** NoCodeAPI's URL-based token is deprecated; official API requires OAuth 2.0.  
