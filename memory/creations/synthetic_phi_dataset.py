```python
import spacy
import numpy as np
import pandas as pd

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# Generate synthetic PHI text with labeled entities
def generate_phi_data(num_samples=1000):
    entities = {
        "PERSON": ["John Doe", "Jane Smith"],
        "ORG": ["Energent Corp", "HealthCo Inc"],
        "DATE": ["2026-04-15", "2025-12-31"],
        "PERCENT": ["94.4%", "72.0%"]
    }
    
    data = []
    for _ in range(num_samples):
        text = f"Patient {np.random.choice(entities['PERSON'])} from {np.random.choice(entities['ORG'])} had a PSA test on {np.random.choice(entities['DATE'])} with {np.random.choice(entities['PERCENT'])} accuracy."
        doc = nlp(text)
        
        # Extract entities
        ents = [(ent.text, ent.label_) for ent in doc.ents]
        data.append({"text": text, "entities": ents})
    
    return pd.DataFrame(data)

# Save to CSV
phi_df = generate_phi_data()
phi_df.to_csv("memory/research/phi_synthetic_dataset.csv", index=False)
```  
