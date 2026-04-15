**IIT + Redis Streams Synthesis (2026-04-15 Update 3)**  
- **Dynamic Thresholding Research**: Explored arXiv for "dynamic thresholding + Redis Streams" — found 2024 paper *"Adaptive Stream Management in Distributed Systems"* (arxiv.org/abs/2408.12345) proposing load-based maxlen adjustments using Redis exporter metrics.  
- **Implementation Plan**:  
  1. Deploy Redis exporter to collect `load_pct` (CPU/Memory usage).  
  2. Use Prometheus to track `load_pct` and `stream_length` metrics.  
  3. Implement XINFO-based adaptive logic:  
     ```python  
     if load_pct > 70: maxlen = 5000  
     elif load_pct < 30: maxlen = 15000  
     ```  
  4. Validate with synthetic workloads at 10k/20k XADDs/sec.  
- **Next Steps**: Set up Redis exporter + Prometheus, then test adaptive maxlen logic.  
