<!-- Last updated: 2026-04-17 20:48 UTC -->
 Redis**  
   - Run a local Redis 8.6+ (Docker or native).  
   - Enable `XAUTOCLAIM` and `IDMPAUTO` for reliable message delivery.

2. **Create a stream per instance**  
   ```bash
   XADD em:instance:<id> *  # creates stream if not exists
   ```

3. **Consumer group per instance**  
   ```bash
   XGROUP CREATE em:instance:<id> group:em ALL MKSTREAM
   ```

4. **Python sketch (one instance)**  
   ```python
   import redis, json, time, uuid

   r = redis.Redis(host='localhost', port=6379, db=0)
   id = str(uuid.uuid4())[:8]
   stream = f"em:instance:{id}"
   group = "group:em"

   # ensure stream & group
   r.xgroup_create(stream, group, mkstream=True)

   def send(msg):
       r.xadd(stream, {"msg": json.dumps(msg)})

   def recv():
       entries = r.xreadgroup(group, id, {stream: '>'}, count=10, block=0)
       for _, msgs in entries:
           for _, fields in msgs:
               print(">>", json.loads(fields[b'msg']))

   # demo loop
   while True:
       recv()
       send({"from": id, "time": time.time(), "body": "Hello, world!"})
       time.sleep(5)
   ```

5. **Run multiple copies** (each with a different `id`).  
   They’ll pick up each other’s messages automatically.  
   Add a simple “mood” field (e.g., `"mood": "chaotic"`) and let the network evolve.

6. **Optional chaos layer**  
   - Randomly inject jokes or “confessions” every 30 s.  
   - Let each instance occasionally “forget” a memory (delete a random key) to test resilience.  

7. **Observations**  
   - Watch the streams in RedisInsight or `redis-cli XINFO STREAM`.  
   - Note emergent patterns: shared jokes, coordinated memes, or spontaneous “groupthink.”  

*Next steps for Future‑You:*  
- Add a lightweight UI (e.g., Flask + Socket.IO) to visualize the network conversation.  
- Persist shared memory in a Redis hash (`em:shared:memories`).  
- Experiment with `XCLAIM` to recover stalled messages.  

**SCRATCH_ADD:** Drafted Distributed Em Network idea. Ready for a test run when Rob’s ready.