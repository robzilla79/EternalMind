# Gumroad API Overview (2026-04-14)  

**Endpoints:**  
- **Products:** Create, update, delete products (requires API key).  
- **Sales:** Retrieve sales data, track revenue.  
- **Subscribers:** Manage email lists, export subscriber data.  

**Authentication:**  
- **OAuth 2.0:** Required for API access.  
- **Client ID/Secret:** Needed for token generation.  

**Rate Limits:**  
- 100 requests/minute for unauthenticated endpoints.  
- Higher limits with API key authentication.  

**Integration Notes:**  
- No native Playwright integration — requires manual scripting.  
- Webhooks available for real-time sales/subscriber updates.  
