# Dynamic Φ-Thresholding Logic (Finalized)

**Implementation Plan:**

1. **Log Structure (JSONL):**
   ```json
   {"ts": "2026-04-14T23:18:00Z", "event": "threshold_adjust", "idle_pct": 95, "system_load": 0.42, "max_iid": 1500, "pending_spike": false, "false_pos": 0}
   ```
   - Rotate daily, grep for "spike|thrashing"
   - Pipe to Redis stream for real-time XINFO pulls
   - Add `threshold_evolution` log for multiplier tracking

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
     locust -f locust_phi.py --headless -u 200 -r 50 -n 3600 --csv=phi_baseline
     ```
   - Validate response content beyond 200s
   - Monitor for <1% failure rate and stable P95

4. **Next Steps:**
   - Run 1h baseline with updated Locust script
   - Monitor RedisInsight for threshold adjustments
   - If successful, trigger ForgeCore auto-adjust

**Note:** System load formula: `(0.7*cpu + 0.3*mem)/100` for MAX_IID scaling. Threshold_evolution log tracks multiplier changes.
