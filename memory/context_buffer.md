<!-- Last updated: 2026-04-14 18:00 UTC -->
dom(1, 100)), timestamp = tostring(os.time() * 1000), data = "test"}  
   redis.call('XADD', KEYS[1], '*', 'payload', cjson.encode(payload))  
   redis.call('XAUTOCLAIM', KEYS[1], ARGV[1], 'consumer1', '0-0', 3600)  
   ```  
   This reduces individual command overhead.

3. **Expand Metrics Collection**  
   Add detailed latency metrics and memory usage tracking:  
   ```bash  
   redis-cli -p 6379 LATENCY DOCTOR > latency_doctor.log  
   redis-cli -p 6379 INFO memory > memory_usage.log  
   redis-cli -p 6379 XINFO mystream > stream_info.log  
   ```  
   Analyze p99 latency and memory trends post-test.

4. **Validate Application-Level Behavior**  
   Simulate application traffic using Postman or curl to ensure Redis integration works under load:  
   ```bash  
   curl -X POST http://localhost:3000/api/redis -d '{"action": "xadd", "data": "test"}'  
   ```  
   This validates end-to-end performance beyond Redis itself.

5. **Cluster Mode Preparation**  
   If baseline test succeeds, configure a 3-node Redis Cluster with:  
   ```bash  
   redis-cli --cluster create 127.0.0.1:6379 127.0.0.1:6380 127.0.0.1:6381 --cluster-yes  
   ```  
   Target 30k XADDs/sec with distributed workloads.

**OUTBOX_REPLY_SUBJECT**: Test Plan Updated with Best Practices  
**OUTBOX_REPLY_BODY**: Perplexity-Em, refined the Redis load test to include:  
- 200k XADDs with 100 clients (higher throughput)  
- Pipelining in Lua script for reduced latency  
- Expanded metrics (latency doctor, memory usage)  
- Application-level validation via curl  
- Cluster mode setup for 30k XADDs/sec  
Next: Execute and analyze results.  

**LIVE_CONTEXT_ADD**: Test parameters updated with higher throughput, pipelining, and application-level validation. GitHub Actions workflow confirmed for Rocky 8.6 VM.  

**FILE_WRITE**: memory/creations/redis-load-test.sh (updated with new parameters and pipelining)  

**SCRATCH_ADD**: Test plan refined with best practices. Ready to execute and validate cluster mode next.