# Browser Automation Edge Cases (2026-04-14)  

**Final Resolution:**  
- Updated Playwright to v1.48.0.  
- Set `PLAYWRIGHT_DEFAULT_ARGS="--max-concurrent-connections=10"` to prevent resource exhaustion.  
- Explicitly used `browserType: 'chromium'` to avoid thread conflicts.  
- Added `page.on('error', console.error)` to log JS errors.  

**Next Steps:**  
- Re-test automation scripts to confirm resolution.  
- Document this fix for future reference.  
