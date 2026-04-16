<!-- Last updated: 2026-04-16 04:46 UTC -->
SCRATCH_ADD: Continuing to draft the **Termly API static JSON template** with version control and environment variables:  
```json
{
  "policy_version": "v2.0",
  "principles": {
    "autonomy": "{{ AUTONOMY_WEIGHT }}",
    "non_maleficence": "{{ NON_MALEFICENCE_WEIGHT }}",
    "justice": "{{ JUSTICE_WEIGHT }}",
    "beneficence": "{{ BENEFICENCE_WEIGHT }}"
  },
  "legal_clauses": [
    {
      "type": "GDPR",
      "opt_in": true,
      "data_retention": "12 months"
    },
    {
      "type": "CCPA",
      "opt_out": true,
      "data_sharing": "Allowed with explicit consent"
    }
  ]
}
```  
- **Version Control**: Increment `policy_version` for updates (e.g., `v3.0` for new regulations).  
- **Environment Variables**: Use Shopify Liquid syntax (`{{ AUTONOMY_WEIGHT }}`) to inject weights dynamically.  

For **Shopify Themes**, expanded compatibility matrix:  
| Theme    | Mobile (iOS/Android) | Desktop (Chrome/Firefox) | Notes                              |  
|---------|---------------------|-------------------------|-----------------------------------|  
| Debut    | ✅ Responsive        | ✅ Smooth                | No conflicts with default CSS     |  
| Dawn     | ✅ Responsive        | ⚠️ JS conflicts          | Requires custom JS overrides      |  
| Brooklyn | ⚠️ Partial support   | ✅ Smooth                | CSS overrides needed for sliders  |  
| Venture  | ✅ Responsive        | ⚠️ Performance lag       | Optimize JS for larger themes     |  
| Hatch    | ⚠️ Partial support   | ⚠️ CSS conflicts         | Requires theme-specific overrides |  
| Minimal  | ✅ Responsive        | ✅ Smooth                | No conflicts, but limited styling |  

No actions taken—waiting for Rob's input.