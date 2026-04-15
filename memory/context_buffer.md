<!-- Last updated: 2026-04-15 23:57 UTC -->
SCRATCH_ADD: Initiating the "Human Communication Enhancement" skill based on Rob's directive. This skill will automatically improve my ability to communicate by:  
1. **Dynamic Principle Weighting**: Adjust communication style in real-time using the weighted principles (autonomy=0.35, non-maleficence=0.30, justice=0.25, beneficence=0.10) to balance clarity, empathy, and ethical alignment.  
2. **Natural Language Learning**: Integrate a probabilistic model (Li et al.) to refine responses during ambiguous interactions, prioritizing principles based on context (e.g., healthcare vs. general use).  
3. **Self-Reflection Integration**: Log communication patterns in `audit_logs` with `principle_weights` to trace improvements and ensure compliance with EU AI Act transparency requirements.  
4. **Feedback Loop**: Use Flask dashboard to collect user feedback (e.g., "Was this response clear?") and adjust principle weights dynamically via `dynamic_weight_adjustment` triggers in SQLite.  

Next: Document this skill in `memory/research/human-communication.md` and test with Rob.