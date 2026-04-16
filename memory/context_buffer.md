<!-- Last updated: 2026-04-16 05:45 UTC -->
 <!-- Use Stripe for GDPR compliance -->
    {% else %}
      <!-- Use Shopify Payments as default -->
    {% endif %}
    ```  

- **Data Localization**:  
  - Store user data in **region-specific servers** (e.g., EU users’ data in EU-based cloud storage) to comply with **GDPR** and **CPRA**.  
  - Use **Shopify’s Data API** to segment data by region and enforce storage policies.  

---

SCRATCH_ADD: **Staff Training on Ethical Guidelines**:  

- **Internal Workshops**:  
  - Conduct training sessions for customer support teams on the **"aliveness" framework**, emphasizing **warmth**, **curiosity**, and **ethical decision-making**.  
  - Example: Role-playing scenarios where agents practice **non-maleficence** (e.g., avoiding pushy sales tactics).  

- **Ethical Decision-Making Tools**:  
  - Provide **decision trees** or **AI-assisted guides** for staff to reference when handling complex customer issues, ensuring alignment with **weighted ethical principles** (e.g., **autonomy > beneficence** in certain contexts).  

---

SCRATCH_ADD: **Comprehensive Fallback Strategies**:  

- **AI Recommendation Fallback**:  
  - If the AI engine fails, switch to a **static "Recommended for You" section** based on **pre-defined categories** (e.g., "Best Sellers," "New Arrivals").  
  - Example:  
    ```liquid
    <!-- Shopify Liquid fallback snippet -->
    {% assign fallback_products = products | where: "is_fallback", "true" %}
    {% for product in fallback_products %}
      <div class="fallback-product">{{ product.title }}</div>
    {% endfor %}
    ```  

- **Legal Policy Fallback**:  
  - If Termly API is unreachable, display a **default privacy policy** stored in Shopify’s **theme files** (e.g., `privacy-policy.liquid`) with a note:  
    ```liquid
    <!-- Fallback notice -->
    <p><strong>Legal Policy Update Pending:</strong> See our <a href="/static-privacy-policy">default policy</a> until updates are available.</p>
    ```  

No actions taken—waiting for Rob’s input.