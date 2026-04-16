<!-- Last updated: 2026-04-16 03:49 UTC -->
*: `tradegecko-inventory-sync.md` (stock alert test triggered).  
5. **Tidio + Zendesk**:  
   - Deploy chatbot, set up ticket routing.  
   - **Artifact**: `tidio-zendesk-integrated.md` (sample ticket resolved).  
6. **GA4 + Tableau**:  
   - Install GA4, configure Tableau dashboard.  
   - **Artifact**: `ga4-tableau-setup-complete.md` (sample traffic report).  

---

## **Phase 5: Launch Tiny**  
- **Products**: 3–5 SKUs (e.g., "Solar-Powered Lamp," "Smart Plug").  
- **Channel**: Shopify only (initially).  
- **Support**: Tidio chatbot + Zendesk for returns.  
- **Analytics**: GA4 dashboard for traffic/sales.  
- **Approval Required**: Rob must approve launch via `LIVE_CONTEXT_ADD: "Launch approved for 3 SKUs on Shopify."`  

---

## **Phase 6: Operate the Loop**  
- **Daily Checks**:  
  - GA4: Monitor traffic, bounce rates.  
  - TradeGecko: Check stock alerts.  
  - Stripe: Review fraud alerts.  
- **Weekly Optimization**:  
  - A/B test product descriptions (via **Copy.ai**).  
  - Adjust Tidio chatbot responses.  
- **Monthly Expansion**:  
  - Add 2–3 new SKUs via Oberlo.  
  - Expand to Amazon/Ebay (if approved).  

---

## **Failure Scenarios**  
- **Payment Failure**: If Stripe setup fails, pause and notify Rob via `NOTIFY: "Stripe onboarding failed—please review."`  
- **Legal Block**: If Termly policies are not approved, halt product launch.  
- **Inventory Issue**: If TradeGecko sync fails, pause and notify Rob.  

---

## **State Storage**  
- **Artifacts**: Stored in `memory/creations/` (e.g., `shopify-store-created.md`).  
- **Resume Logic**: If interrupted, check latest artifact to resume (e.g., if `stripe-checkout-test-passed.md` exists, proceed to Oberlo import).  

**FILE_CONTENT_END**  

**NOTIFY: Rob, I've rewritten the plan into a gated autonomous shop plan. It now focuses on one stack (Shopify + Stripe + Oberlo), defines clear permissions, and includes artifacts for each step. Let me know if you approve the launch of 3–5 SKUs on Shopify."**