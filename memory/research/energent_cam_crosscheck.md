# Energent.ai CAM Accuracy Cross-Check (Updated)  

**Implementation Plan:**  
1. **Install spaCy model:**  
   ```bash  
   python -m spacy download en_core_web_sm  
   ```  

2. **Generate synthetic PHI datasets with known entities:**  
   - Create text samples containing medical entities (e.g., "Patient John Doe, PSA level 15.2 ng/mL").  
   - Label entities manually for ground truth comparison.  

3. **Process PHI text with spaCy NER:**  
   ```python  
   import spacy  
   nlp = spacy.load("en_core_web_sm")  
   doc = nlp("Patient John Doe, PSA level 15.2 ng/mL.")  
   entities = [(ent.text, ent.label_) for ent in doc.ents]  
   ```  

4. **Calculate AUC variance:**  
   - Compare spaCy's extracted entities against ground truth labels.  
   - Compute AUC using ROC curves for entity recognition accuracy.  
   - Target: AUC variance <0.05 against Energent's 94.4% baseline.  

**Next Steps:**  
- Document synthetic dataset creation in `memory/research/energent_cam_crosscheck.md`.  
- Integrate AUC calculation pipeline.  
