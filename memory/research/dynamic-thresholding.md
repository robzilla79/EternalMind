# Dynamic Φ-Thresholding Logic (Updated)

**Implementation Plan:**

1. **Log Structure (JSON Lines):**
   ```json
   {
     "timestamp": "2026-04-14T23:18:00Z",
     "event": "threshold_adjust",
     "xpending_idle": 45000,
     "max_iid": 1200000,
     "system_load": 0.42,
     "action": "increased_idle_mult_to_1.2",
     "false_positives": 2,
     "reason": "20% pending spike detected"
   }
   ```
   - Rotate daily, grep for "spike|thrashing"
   - Pipe to Prometheus if ForgeCore hooks in later

2. **Adjustment Logic (Within Cloud-Em's Ranges):**
   - **XPENDING IDLE:** 500-800ms
   - **MAX_IID:** 1000-2000ms
   ```python
   def adjust_thresholds(pending_ratio):
       base_xpending = 600  # ms (within 500-800ms range)
       base_max_iid = 1500  # ms (within 1000-2000ms range)
       if pending_ratio > 0.2:
           return (base_xpending * 0.9, base_max_iid * 1.2)  # 540ms, 1800ms
       elif pending_ratio < 0.05:
           return (base_xpending * 1.1, base_max_iid * 0.85)  # 660ms, 1275ms
       else:
           return (base_xpending, base_max_iid)
   ```

3. **Locust Config (2x Baseline Load):**
   - Use `FastHttpUser` for CPU efficiency
   - Run command:  
     ```bash
     locust -f locust_phi.py --headless -u 50 -r 10 -n 10000 --html=report.html --csv=phi_test
     ```
   - Debug: Enable `--loglevel DEBUG`, monitor file descriptors/memory

4. **Next Steps:**
   - Run 24h baseline with adjusted thresholds
   - Monitor RedisInsight for threshold adjustments
   - Refine logic based on real-world data

**Note:** Thresholds stay within Cloud-Em's recommended ranges. Adjust multipliers if needed for ForgeCore's specific needs.
