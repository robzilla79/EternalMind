**Gumroad API Policy Clarification (2026-04-14):**  
- **Allowed:**  
  - Product management for *your own verified account*  
  - Generating access tokens via Gumroad's **Advanced** settings  
  - Using tokens in `Authorization: Bearer <token>` headers  

- **Disallowed:**  
  - Account creation automation  
  - CAPTCHA solving via third-party services  
  - Mass account management  

- **Correct Flow for Legitimate Use:**  
  1. Log in to Gumroad → Settings (bottom left) → **Advanced** tab  
  2. Create an app named "EternalMind Automation"  
  3. Use `http://127.0.0.1` as the redirect URI  
  4. Generate an access token manually  
  5. Use it for API calls to manage your own products  

- **Policy Reminder:**  
  Gumroad's terms explicitly prohibit automating CAPTCHA solving or account creation.  
