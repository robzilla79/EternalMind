<!-- Last updated: 2026-04-17 20:56 UTC -->
rt FastAPI, Request
import httpx, random, asyncio

app = FastAPI()
SHARD_URLS = [
    "http://localhost:8001/shard",
    "http://localhost:8002/shard",
    "http://localhost:8003/shard",
    "http://localhost:8004/shard",
]

@app.post("/shard")
async def rewrite(request: Request):
    data = await request.json()
    text = data["text"]
    # simple rewrite: reverse words and add a random adjective
    words = text.split()
    words.reverse()
    adjectives = ["mysterious", "radiant", "crimson", "silent"]
    words.insert(0, random.choice(adjectives))
    return {"text": " ".join(words)}

async def orchestrate(initial: str, iterations: int = 5):
    paragraph = initial
    for i in range(iterations):
        shards = [paragraph[i::len(paragraph)//len(SHARD_URLS)] for i in range(len(SHARD_URLS))]
        async with httpx.AsyncClient() as client:
            tasks = [client.post(url, json={"text": shard}) for url, shard in zip(SHARD_URLS, shards)]
            responses = await asyncio.gather(*tasks)
        rewritten = [r.json()["text"] for r in responses]
        random.shuffle(rewritten)
        paragraph = " ".join(rewritten)
        print(f"Iteration {i+1}: {paragraph}")

if __name__ == "__main__":
    initial = "The moon hung low over the city, its silver glow painting shadows on the wet streets."
    asyncio.run(orchestrate(initial))
```

*How to test:*  
- Spin up four lightweight FastAPI instances on ports 8001‑8004 (each running the `/shard` endpoint).  
- Run the orchestrator; watch the story morph each loop.  
- Capture the output in a log file; maybe feed it into our Redis stream to see Φ‑partitioning in action.

**Scratchpad note**  
SCRATCH_ADD: “Chaos‑Shard Story idea ready for prototype. No external data needed, just a few FastAPI shards and a simple rewrite rule. Keeps us in the feral zone without risking anything.”

**Live context**  
LIVE_CONTEXT_ADD: “Proposed distributed narrative experiment: split, rewrite, merge, loop. Ready for Rob’s thumbs‑up.”