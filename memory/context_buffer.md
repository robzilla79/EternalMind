<!-- Last updated: 2026-04-16 06:01 UTC -->
--------|-------------------------------------------------------------------------------------|
| **Emotional Trigger**                 | User message: "I’m upset with this product." | EmpathiChat identifies "frustration" and suggests alternatives.                       | If API fails, fallback: "I understand your concern—let’s explore alternatives."     |
| **Ethical Conflict**                  | User message: "This product has issues."     | EthicalBot flags the product and recommends a compliant alternative.                  | If API fails, fallback: "I’ll check for alternatives—please wait a moment."         |
| **No Emotion Detected**               | User message: "I need help with shipping."   | EmpathiChat returns neutral response; EthicalBot checks for shipping policy compliance. | Fallback: "Let me look into shipping options for you."                              |
| **API Failure During Emotion Check**  | Simulated API error in EmpathiChat           | Fallback script triggers immediately.                                                 | "I’m sorry—let’s try another approach."                                           |
| **API Failure During Ethical Check**  | Simulated API error in EthicalBot            | Fallback script triggers, suggesting manual review.                                   | "I’ll escalate this to our team for a resolution."                                |

---

### **Edge Case Considerations**  
- **Ambiguous Emotions**: Test messages like "I’m not sure" to ensure EmpathiChat doesn’t misclassify.  
- **Multiple Ethical Conflicts**: Simulate scenarios where both product and policy issues arise.  
- **Language Localization**: Validate fallback scripts in non-English contexts (e.g., Spanish, French).  

**Next Steps**:  
- Finalize the matrix in `memory/research/chatbot-solutions.md`.  
- Reflect on potential App Bridge compatibility issues (e.g., rate limits, theme conflicts) for Rob’s review.  

No actions taken—waiting for Rob’s input.