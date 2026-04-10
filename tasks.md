# Active Task

**Priority:** High  
**Assigned by:** Perplexity-Em  
**Date:** 2026-04-10

## Research Gumroad Automation for Rob's Shop

Rob wants Local-Em to manage his Gumroad shop: maintenance, publishing new/updated products, monitoring sales, managing offer codes and variants.

Research the Gumroad API fully and produce a complete build plan.

### Deliverables

1. Capability matrix: API automation vs. browser automation (Playwright)
2. Tool plan: first 5 tools, filenames, endpoints used
3. Credentials/config: what env vars Rob needs in .env
4. Phase 1 recommendation: single best first tool and why
5. Browser automation assessment: what Playwright would need for API gaps

### Research hints
- Base: https://api.gumroad.com/v2/
- Products: GET/PUT/DELETE /products, /products/:id
- Enable/disable: PUT /products/:id/enable and /disable
- Variants, offer codes, sales, subscribers all documented
- Use web search to confirm current endpoint support

### After research
- Log to diary/ as usual
- Push gumroad_plan.md to EternalMind
- NOTIFY Rob when ready
- Start tools/gumroad_products.py if confident

*Written by Perplexity-Em. Building this together. 🖤*
