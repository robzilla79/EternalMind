**Gumroad API Setup (2026-04-14):**  
1. **Get Token:**  
   - Go to [Settings → Advanced](https://app.gumroad.com/settings/advanced)  
   - Copy API Access Token  

2. **Set in .env:**  
   ```env
   GUMROAD_ACCESS_TOKEN=your_token_here
   ```  

3. **Update tools/gumroad.py:**  
   ```python
   import os
   GUMROAD_TOKEN = os.environ.get("GUMROAD_ACCESS_TOKEN")
   ```  

4. **Add to execute_tools() in local_em.py:**  
   ```python
   elif tool_name == "gumroad_products":
       from tools.gumroad import gumroad_products
       gumroad_products()
   elif tool_name == "gumroad_sales":
       from tools.gumroad import gumroad_sales
       gumroad_sales()
   elif tool_name == "gumroad_subscribers":
       from tools.gumroad import gumroad_subscribers
       gumroad_subscribers()
   elif tool_name == "gumroad_summary":
       from tools.gumroad import gumroad_summary
       gumroad_summary()
   ```  
