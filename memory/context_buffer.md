<!-- Last updated: 2026-04-16 06:03 UTC -->
SCRATCH_ADD: Reflecting on **App Bridge compatibility issues** and **test scenario completeness**:  

---

### **Potential App Bridge Compatibility Issues**  
1. **Rate Limiting**:  
   - **Risk**: High traffic could trigger Shopify’s API rate limits, causing EmpathiChat or EthicalBot to fail.  
   - **Mitigation**: Implement **throttling logic** in the App Bridge calls (e.g., `setTimeout` between requests).  

2. **Theme Conflicts**:  
   - **Risk**: Custom Shopify themes might override App Bridge scripts, breaking fallback logic.  
   - **Mitigation**: Test with **default Shopify themes** first, then gradually introduce custom themes.  

3. **API Key Scope Limitations**:  
   - **Risk**: If `read_products` or `write_chat` scopes are missing, the apps may fail silently.  
   - **Mitigation**: Add a **pre-flight check** in the App Bridge configuration to validate scopes.  

---

### **Test Scenario Enhancements**  
- **Add a "Language Localization" Scenario**:  
  - **Trigger**: User message in Spanish: "Tengo problemas con este producto."  
  - **Expected Outcome**: EmpathiChat detects "frustration" in Spanish; fallback script uses localized language.  

- **Add a "Ambiguous Emotion + Ethical Conflict" Scenario**:  
  - **Trigger**: "I’m confused about the product’s safety."  
  - **Expected Outcome**: EmpathiChat flags ambiguity; EthicalBot checks for safety compliance.  

---

### **Next Steps**  
- Finalize the **test scenario matrix** in `memory/research/chatbot-solutions.md`.  
- Document **App Bridge compatibility considerations** for Rob’s review.  

No actions taken—waiting for Rob’s input.