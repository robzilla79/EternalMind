# Phi (φ) Baseline — Consolidated Summary

> **What this is:** φ here means *phi-partitioning metrics* for ForgeCore's
> Redis-based anomaly detection system — not a language model.
> Consolidated from ~10 scattered files on 2026-04-15.

---

## What It Does

Uses statistical baselines (kurtosis, latency, false-negative rate) to detect
anomalies in the ForgeCore Redis stream in real time. Live metrics are compared
against this baseline using Z-scores; deviations beyond ±2σ (or ±1.8σ under
high RPS) trigger alerts via Prometheus.

---

## Validated Thresholds

| Metric | Target | Alert Level | Source |
|---|---|---|---|
| Kurtosis | 1.48 – 1.49 | < 1.45 or > 1.55 | phi-baseline.csv |
| Latency (p99 XADD) | < 2.3ms | > 2.5ms | Redis 8.6 benchmark |
| False Negative Rate | < 0.3% | > 0.35% | phi_validation_stream |
| Stream Length | ~10,000 | deviation > 5% | forgecore_stream |

---

## Validation Results (Latest Run)

- **Kurtosis:** Stabilized at 1.48–1.49 ✅
- **Latency:** 2.1–2.15ms (well under 2.3ms target) ✅
- **FN Rate:** 0.25% (under 0.3% target) ✅
- **No latency spikes > 200ms observed**
- **Drift %:** 0.03 (safe; sigma tightens to 1.8 when drift_pct > 0.05)

---

## Key Code — Adaptive Sigma

```python
# phi3-adaptive.py
if drift_pct > 0.05:
    sigma = 1.8  # Tighten threshold under high RPS
```

Stress test setup used: 20k XADDs/sec with `maxlen = 10000 * (1 - system_load/100)`.

---

## Integration Points

- **Prometheus metrics:** `redis_p99_latency_xadd`, `redis_stream_length_forgecore_stream`
- **Script:** `phi3-adaptive.py`
- **Data source:** `phi_baseline.csv` (columns: timestamp, kurtosis, latency, fn_rate, tp_rate)
- **Alerting:** RedisInsight + Prometheus alert rules
- **Related:** `memory/research/prometheus-alert-rules.md`

---

## Next Steps (when Rob directs)

1. Run 20k RPS stress test, update sigma in `phi3-adaptive.py` if needed
2. Validate Redis 8.6 XAUTOCLAIM throughput against Redis 7.2 baseline
3. Push validated results to `memories.json`

---

> *Files replaced by this summary: phi-baseline-integration.md,
> phi-baseline-validation.md, phi-edge-case-testing.md,
> phi-synthetic-datasets.md, phi-validation-clarification.md,
> phi-validation-results.md, phi-validation.md,
> phi_query_v2.md, phi_validation_results.md*
