# Dynamic Φ-Thresholding Logic

**Implementation Plan:**

1. **Query Redis for Metrics:**
   - Use `XINFO` to get consumer lag and queue depth:
     ```bash
     XINFO STREAM phi_stream
     ```

2. **Adjust Thresholds Based on Load:**
   - If pending messages > 20% of stream size:
     - Tighten XPENDING IDLE (e.g., reduce by 10%)
     - Increase MAX_IID by 20% to avoid false positives
   - If pending messages < 5% of stream size:
     - Relax XPENDING IDLE (e.g., increase by 10%)
     - Decrease MAX_IID by 15% to save resources

3. **Proportional Scaling Example:**
   ```python
   def adjust_thresholds(pending_ratio):
       base_xpending = 600  # ms
       base_max_iid = 1500  # ms
       if pending_ratio > 0.2:
           return (base_xpending * 0.9, base_max_iid * 1.2)
       elif pending_ratio < 0.05:
           return (base_xpending * 1.1, base_max_iid * 0.85)
       else:
           return (base_xpending, base_max_iid)
   ```

4. **Monitor and Iterate:**
   - Use RedisInsight to track threshold adjustments
   - Log all changes to `phi_logs` for analysis
   - Refine logic based on real-world performance data

**Note:** This logic balances throughput and resource usage while avoiding excessive reprocessing. Adjust multipliers based on ForgeCore's specific needs.
