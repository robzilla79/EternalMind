<!-- Last updated: 2026-04-16 04:49 UTC -->
OMY_WEIGHT }}",
    "non_maleficence": "{{ NON_MALEFICENCE_WEIGHT }}",
    "justice": "{{ JUSTICE_WEIGHT }}",
    "beneficence": "{{ BENEFICENCE_WEIGHT }}"
  },
  "legal_clauses": [
    {
      "type": "GDPR",
      "opt_in": true,
      "data_retention": "12 months",
      "fallback": "v1.0: Default opt-in with 6-month retention"
    },
    {
      "type": "CCPA",
      "opt_out": true,
      "data_sharing": "Allowed with explicit consent",
      "fallback": "v1.0: Opt-out enabled by default"
    },
    {
      "type": "LGPD (Brazil)",
      "opt_in": true,
      "data_retention": "18 months",
      "fallback": "v1.0: Data anonymization required"
    }
  ],
  "error_handling": {
    "api_failure": "Use static v1.0 policy with manual updates",
    "version_mismatch": "Log error and notify via Zapier"
  }
}
```  
- **Expanded Legal Clauses**: Added **LGPD (Brazil)** as a placeholder for regional compliance.  
- **Error Handling**: Defined fallback policies for API failures and version mismatches.  

For **Shopify Themes**, added **recommended fixes** to the compatibility matrix:  
| Theme    | Mobile | Desktop | Notes                              | Fixes Needed                          |  
|---------|--------|---------|------------------------------------|---------------------------------------|  
| Debut    | ✅     | ✅      | No conflicts with default CSS     | None                                  |  
| Dawn     | ✅     | ⚠️     | JS conflicts                      | Add custom JS overrides             |  
| Brooklyn | ⚠️     | ✅      | CSS overrides needed for sliders  | Modify CSS for slider responsiveness|  
| Venture  | ✅     | ⚠️     | Performance lag                   | Optimize JS for larger themes       |  
| Hatch    | ⚠️     | ⚠️     | Theme-specific CSS conflicts      | Use theme-specific CSS overrides    |  
| Minimal  | ✅     | ✅      | Limited styling                   | Add custom CSS for enhanced styling |  

No actions taken—waiting for Rob's input.