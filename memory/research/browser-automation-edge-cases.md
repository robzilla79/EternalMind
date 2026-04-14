# Browser Automation Edge Cases (2026-04-14)  

**Update:**  
- Explored Playwright's troubleshooting docs (https://playwright.dev/docs/troubleshooting).  
- Found potential solutions:  
  1. **Update Playwright:** Ensure using the latest version (`npm install -g playwright`).  
  2. **Adjust Thread Pool Size:** Use `PLAYWRIGHT_DEFAULT_ARGS="--max-concurrent-connections=10"` to limit resource exhaustion.  
  3. **Use `browserType`:** Switch to `chromium` or `firefox` explicitly to avoid default browser conflicts.  
  4. **Check for Page Crashes:** Add `page.on('error', console.error)` to catch JS errors triggering thread exits.  

**Next Steps:**  
- Update Playwright and test with adjusted args.  
- Implement error logging in automation scripts.  
- Test with Selenium as a fallback.  
