```python
import redis
import pandas as pd

# Connect to Redis
r = redis.Redis(host='localhost', port=6379, db=0)

# Load synthetic data
phi_df = pd.read_csv("memory/research/phi_synthetic_dataset.csv")

# Inject into Redis stream
stream_key = "phi_validation_stream"
for index, row in phi_df.iterrows():
    data = {
        "text": row["text"],
        "entities": row["entities"]
    }
    r.xadd(stream_key, data, id="*", maxlen=10000, trim="MAXLEN")
```  
