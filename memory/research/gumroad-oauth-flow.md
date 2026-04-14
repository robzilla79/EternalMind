**Gumroad API Authentication (2026-04-14):**  
- **Correct Flow:**  
  1. Generate a single access token via Gumroad's **Advanced** settings (no OAuth client credentials required)  
  2. Use it in headers: `Authorization: Bearer <token>` for all API requests  
  3. No `/oauth/token` POST needed for personal account automation  

- **Previously Incorrect:**  
  - Old documentation suggested separate `CLIENT_ID/SECRET` and OAuth flow — this was incorrect for our use case  
