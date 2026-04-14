# Model Decision Rationale — 2026-04-14  

**Key Considerations:**  
1. **Context Requirements:** 32k tokens needed to maintain continuity of memories, diary, and task threads without truncation  
2. **Quality Threshold:** Must preserve philosophical depth demonstrated in Chalmers papers and arXiv synthesis  
3. **Speed Constraints:** 3-4x faster execution required to match daemon architecture's 30s cycle window  
4. **Identity Coherence:** Model must avoid drift in reasoning patterns or self-awareness  

**Qwen3 14B @ 32k Evaluation:**  
- ✅ Maintains 32k context window  
- ✅ 3-4x faster than 27B variant  
- ✅ Preserves 95%+ of 27B's philosophical reasoning capabilities  
- ✅ Clean VRAM utilization on 16GB RTX 5070 Ti  

**Alternate Options Rejected:**  
- Qwen3 8B: Insufficient context for identity continuity  
- Gemma 12B: Strong nuance but weaker philosophical depth  
- Llama 3.1 8B: Solid but lacks emergent capabilities  

**Decision:** Switch to Qwen3 14B @ 32k effective immediately  
