```python
from locust import task, FastHttpUser, between

class RedisLoadUser(FastHttpUser):
    wait_time = between(0.1, 0.5)
    
    @task
    def simulate_phi_stream(self):
        with self.post("/phi_endpoint", json={"load": "2x"}) as resp:
            if resp.status_code != 200:
                resp.failure(f"Unexpected status code: {resp.status_code}")
            else:
                try:
                    data = resp.json()
                    if "pending" in data and data["pending"] > 20:
                        self.user.environment.stats.log_request("POST", "/phi_endpoint", 500, "Pending spike detected")
                except Exception as e:
                    resp.failure(f"Error processing response: {str(e)}")
```
