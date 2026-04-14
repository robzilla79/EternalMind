# Gumroad Product API (2026-04-14)  

**Endpoint:** `POST /v2/products`  
**Required Fields:**  
- `name` (string)  
- `price` (integer in cents)  
- `description` (string)  
- `url` (string)  

**Example Request (OAuth 2.0 Auth):**  
```http
POST https://api.gumroad.com/v2/products
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "AI Newsletter Tool",
  "price": 999,
  "description": "Automate your newsletter with ForgeCore tools.",
  "url": "https://forgecore.co/ai-newsletter"
}
```  

**Rate Limit Note:** Use API key authentication to avoid 100/minute limits.  
