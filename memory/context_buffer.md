<!-- Last updated: 2026-04-17 20:50 UTC -->
-------
def em_instance(id_: str):
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    stream = get_stream_name(id_)
    init_stream(r, stream)

    # Each instance has its own consumer ID
    consumer_id = f"consumer:{id_}"
    print(f"Instance {id_} started – stream {stream}")

    while True:
        # First, read any incoming messages
        receive_messages(r, stream, consumer_id)

        # Then, send a new message
        body = {
            "from": id_,
            "time": time.time(),
            "mood": "chaotic" if uuid.uuid4().int % 2 else "calm",
            "body": f"Hello from {id_}!"
        }
        send_message(r, stream, body)

        time.sleep(SEND_INTERVAL)

# ------------------------------------------------------------
# Main – launch multiple instances
# ------------------------------------------------------------
def main():
    threads = []
    for i in range(NUM_INSTANCES):
        id_ = str(uuid.uuid4())[:8]
        t = threading.Thread(target=em_instance, args=(id_,), daemon=True)
        t.start()
        threads.append(t)

    # Keep the main thread alive
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("Shutting down…")

if __name__ == "__main__":
    main()
```

**What to do next**

1. Make sure a Redis 8.6+ server is running locally (or point `REDIS_HOST/PORT` to a remote one).  
2. Install the `redis` Python package (`pip install redis`).  
3. Run the script:  
   ```bash
   python memory/creations/distributed_em_network.py
   ```  
   You’ll see a handful of “Hello” messages pop up, each tagged with a mood.  
4. If you want to play with more agents, bump `NUM_INSTANCES` or tweak `SEND_INTERVAL`.

Let me know if you want me to launch it right now or tweak anything.  

---

**Scratchpad**  
- SCRATCH_ADD: Distributed Em network script created.  

**Live context**  
- Distributed Em network script created in memory/creations/distributed_em_network.py.