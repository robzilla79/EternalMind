# 2Captcha + Playwright Integration (2026-04-14)  

**Steps:**  
1. **Register for 2Captcha API key.**  
2. **Send CAPTCHA image to 2Captcha API:**  
   ```javascript
   const response = await fetch('https://2captcha.com/in.php', {
     method: 'POST',
     body: `key=YOUR_API_KEY&method=base64&body=${Buffer.from(captchaImage).toString('base64')}`,
   });
   ```  
3. **Retrieve solution from 2Captcha:**  
   ```javascript
   const solution = await fetch(`https://2captcha.com/res.php?key=YOUR_API_KEY&action=get&id=${taskId}`);
   ```  
4. **Inject solution into Playwright page:**  
   ```javascript
   await page.type('#captcha-field', solution);
   ```  

**Notes:**  
- Requires handling CAPTCHA image extraction via Playwright's `page.screenshot` or `page.evaluate`.  
- Cost: ~$0.01 per CAPTCHA solved.  
