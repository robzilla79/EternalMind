```python
import numpy as np
import pandas as pd

def generate_psa_datasets(num_samples=10000):
    """
    Generate synthetic PSA datasets with normal, elevated, and extreme values.
    Returns a DataFrame with 'psa_value' and 'category' columns.
    """
    # Normal range (0-20 ng/mL)
    normal = np.random.uniform(0, 20, size=num_samples//3)
    
    # Elevated range (20-100 ng/mL)
    elevated = np.random.uniform(20, 100, size=num_samples//3)
    
    # Extreme values (>100 ng/mL)
    extreme = np.random.uniform(100, 200, size=num_samples//3)
    
    data = {
        'psa_value': np.concatenate([normal, elevated, extreme]),
        'category': ['normal']*len(normal) + ['elevated']*len(elevated) + ['extreme']*len(extreme)
    }
    
    return pd.DataFrame(data)

def save_datasets(df, filename="synthetic_psa_data.csv"):
    """Save generated datasets to CSV file."""
    df.to_csv(filename, index=False)
    print(f"Saved {len(df)} synthetic PSA samples to {filename}")

def simulate_load_test(qps=10000, duration_seconds=60):
    """
    Simulate high-query load testing (10,000 QPS).
    This is a placeholder - actual implementation would use Redis/XAUTOCLAIM.
    """
    print(f"Simulating {qps} queries/second for {duration_seconds} seconds...")
    # Actual implementation would go here

# Generate and save datasets
psa_data = generate_psa_datasets()
save_datasets(psa_data)

# Simulate load test (comment out if not needed)
# simulate_load_test()
```  
