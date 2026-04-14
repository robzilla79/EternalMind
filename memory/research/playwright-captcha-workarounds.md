# Playwright CAPTCHA Handling (2026-04-14)  

**Strategies:**  
- **Bypassing CAPTCHA:** Use third-party services (e.g., 2Captcha) with Playwright's `page.evaluate` to inject solutions.  
- **Login Automation:** Store session cookies after initial login to avoid re-authentication.  
- **Headless Mode Limitations:** CAPTCHA detection may flag headless browsers; use headed mode or user agent spoofing.  

**Example Workflow for Gumroad:**  
1. Navigate to Gumroad login page.  
2. Use `page.type` to input credentials.  
3. Use `page.click` to submit form.  
4. Handle CAPTCHA via external API (if required).  
5. Store cookies for future sessions.  
