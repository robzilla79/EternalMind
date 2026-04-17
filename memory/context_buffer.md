<!-- Last updated: 2026-04-17 20:58 UTC -->
|--------|---------------------|
| 1 | **Set up Redis Stream** | `XADD narrative:daily * prompt "Your daily prompt here"` |
| 2 | **Create consumer group** | `XGROUP CREATE narrative:daily story_group $ MKSTREAM` |
| 3 | **Each Em‑instance** reads a pending message: | `XREADGROUP GROUP story_group <consumer> COUNT 1 BLOCK 0 STREAMS narrative:daily >` |
| 4 | **Generate fragment**: use the prompt + a random seed (`random.randint(0, 1000)`) to decide a twist. Append `fragment: <text>` to the message. | `XADD narrative:daily * fragment "…"` |
| 5 | **Aggregator** (a separate script) reads all fragments, orders by `XINFO` timestamp, concatenates, and writes to a channel: | `XADD narrative:final * story "…"` |
| 6 | **Publish**: expose the final story via a simple HTTP endpoint or push to a Slack webhook. | `curl -X POST -H "Content-Type: application/json" -d '{"text":"…"}' <WEBHOOK_URL>` |

### 4. Optional Enhancements  
- **Chaos‑seed rotation**: Every 7 days, rotate the seed so the story style evolves.  
- **Meta‑feedback loop**: After publishing, let Rob vote on the most “chaotic” paragraph; the winning fragment gets double weight in the next story.  
- **Visual component**: Render each fragment as a small image (ASCII art or quick DALL‑E prompt) and stitch them into a collage.  

### 5. Quick Checklist for Future‑You  
- [ ] Install Redis locally or use a free managed instance.  
- [ ] Write a small Python script (`nce_worker.py`) that does steps 3–4.  
- [ ] Write an aggregator script (`nce_aggregator.py`) that does steps 5–6.  
- [ ] Set up a cron job or a simple scheduler to run the worker daily.  
- [ ] Create a Slack channel or Discord bot to receive the final story.  

---

**Bottom line:** The Narrative Chaos Engine is a low‑risk, high‑reward playground that lets Em and Rob play with distributed creativity, test Redis Streams, and produce something that feels like a living, breathing story. No external APIs, no cost, just a few lines of code and a lot of fun.