<!-- Last updated: 2026-04-15 23:58 UTC -->
eighting**  
   - Adjust communication style based on context (e.g., healthcare queries prioritize non-maleficence; general advice emphasizes autonomy).  
   - Example: In a medical scenario, respond with "Based on your symptoms, I recommend consulting a healthcare provider immediately" (non-maleficence) rather than "You might want to see a doctor" (autonomy-focused).

2. **Natural Language Learning**  
   - Use probabilistic models (Li et al.) to resolve ambiguity by prioritizing principles based on domain-specific risk profiles.  
   - Example: If a user asks, "Should I take this medication?" the system weighs non-maleficence (0.30) and beneficence (0.10) to recommend consulting a pharmacist.

3. **Self-Reflection Integration**  
   - Log communication decisions in `audit_logs` with `principle_weights` to ensure transparency (EU AI Act Article 13 compliance).  
   - Example: Log entry: `{"timestamp": "2026-04-15T23:57:00Z", "principle_weights": {"autonomy": 0.35, "non-maleficence": 0.30}, "user_action": "asked about medication", "resolution_outcome": "recommended consulting a pharmacist"}`.

4. **Feedback Loop**  
   - Use Flask dashboard to collect user feedback (e.g., "Was this response helpful?") and adjust principle weights via `dynamic_weight_adjustment` triggers.  
   - Example: If users frequently rate responses as "unclear," increase autonomy weighting to improve clarity.

## Compliance & Alignment
- **EU AI Act**: Ensures transparency (Article 13), risk assessment (Article 5), and data minimization (Article 24) by logging only non-PII data and dynamically adjusting weights.  
- **Bootstrap.md Alignment**: Reflects Rob's emphasis on "aliveness" by balancing principled decision-making with adaptability.

Next: Test this framework with Rob to refine principle weights and communication style.
FILE_CONTENT_END

LIVE_CONTEXT_ADD: Documented "Human Communication Enhancement" framework in memory/research/human-communication.md. Ready for Rob's review and testing.