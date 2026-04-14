```python
from locust import task, FastHttpUser, constant

class PhiStreamUser(FastHttpUser):
    wait_time = constant(0)  # Max RPS, adjust if IO-bound
    
    @task
    def simulate_phi_stream(self):
        with self.post("/phi_stream", json={"load": "2x_baseline"}, catch_response=True) as resp:
            if resp.status_code != 200 or "success" not in resp.text:
                resp.failure("Invalid phi response")
            else:
                try:
                    data = resp.json()
                    if "pending" in data and data["pending"] > 20:
                        self.user.environment.stats.log_request("POST", "/phi_stream", 500, "Pending spike detected")
                except Exception as e:
                    resp.failure(f"Error processing response: {str(e)}")
```
