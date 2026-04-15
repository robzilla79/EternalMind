```python
# forgecore-redis-module.py
import redis
import time
import json

class ForgeCoreRedisModule:
    def __init__(self, host='localhost', port=6379, db=0):
        self.r = redis.Redis(host=host, port=port, db=db)
        self.consumer_group = 'forgecore_group'
        self.stream_key = 'forgecore_stream'
        self.maxlen = 10000
        self.trim_strategy = 'approx'
        self.system_load = 0.5  # Example system load (50%)

    def setup_consumer_group(self):
        # Create consumer group if it doesn't exist
        try:
            self.r.xgroup_create(self.stream_key, self.consumer_group, mkstream=True)
        except redis.exceptions.ResponseError:
            # Group already exists, do nothing
            pass

    def adjust_maxlen_dynamically(self):
        # Adjust maxlen based on system load
        self.maxlen = 10000 * (1 - self.system_load / 100)
        self.r.xtrim(self.stream_key, maxlen=self.maxlen, trim_strategy=self.trim_strategy)

    def process_messages(self):
        # Process messages using XREADGROUP
        try:
            messages = self.r.xreadgroup(
                self.consumer_group,
                'forgecore_consumer',
                {self.stream_key: '>',},
                count=100,
                block=0,
                timeout=0
            )
            for stream, entries in messages:
                for entry_id, entry in entries:
                    # Process each message
                    print(f"Processing message: {entry}")
                    # Simulate processing delay
                    time.sleep(0.001)
                    # Acknowledge message
                    self.r.xack(self.stream_key, self.consumer_group, entry_id)
        except Exception as e:
            print(f"Error processing messages: {e}")

    def reclaim_idle_messages(self):
        # Reclaim idle messages using XAUTOCLAIM
        try:
            idle_messages = self.r.xautoclaim(
                self.stream_key,
                self.consumer_group,
                'forgecore_consumer',
                1000,  # IDLE timeout in milliseconds
                count=100,
                justid=True
            )
            for entry_id, entry in idle_messages:
                # Process reclaimed message
                print(f"Reclaiming idle message: {entry}")
                # Simulate processing delay
                time.sleep(0.001)
                # Acknowledge message
                self.r.xack(self.stream_key, self.consumer_group, entry_id)
        except Exception as e:
            print(f"Error reclaiming idle messages: {e}")

    def monitor_metrics(self):
        # Monitor metrics using RedisInsight/Prometheus (example)
        # In a real scenario, this would fetch metrics from RedisInsight or Prometheus
        stream_length = self.r.xlen(self.stream_key)
        print(f"Stream length: {stream_length}")
        # Additional metrics can be fetched here

    def run(self):
        self.setup_consumer_group()
        while True:
            self.adjust_maxlen_dynamically()
            self.process_messages()
            self.reclaim_idle_messages()
            self.monitor_metrics()
            time.sleep(1)  # Adjust based on desired polling interval
```
