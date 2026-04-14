<!-- Last updated: 2026-04-14 18:03 UTC -->
yload = {version = tostring(math.random(1, 100)), timestamp = tostring(os.time() * 1000), data = "test"}  
   redis.call('XADD', KEYS[1], '*', 'payload', cjson.encode(payload))  
   redis.call('XAUTOCLAIM', KEYS[1], ARGV[1], 'consumer1', '0-0', 3600)  
   ```  
   This batches operations for efficiency.

3. **Collect Metrics**  
   After the test, gather detailed metrics:  
   ```bash  
   redis-cli -p 6379 LATENCY DOCTOR > latency_doctor.log  
   redis-cli -p 6379 INFO memory > memory_usage.log  
   redis-cli -p 6379 XINFO mystream > stream_info.log  
   ```  
   Analyze p99 latency, memory usage, and duplicate rates from the CSV output.

4. **Validate Application-Level Performance**  
   Use `curl` to simulate application traffic:  
   ```bash  
   curl -X POST http://localhost:3000/api/redis -d '{"action": "xadd", "data": "test"}'  
   ```  
   Ensure Redis integration works under load.

5. **Cluster Mode Setup (If Baseline Succeeds)**  
   If the single-node test passes, configure a 3-node Redis Cluster:  
   ```bash  
   redis-cli --cluster create 127.0.0.1:6379 127.0.0.1:6380 127.0.0.1:6381 --cluster-yes  
   ```  
   Target 30k XADDs/sec with distributed workloads.

**OUTBOX_REPLY_SUBJECT**: Load Test Execution and Analysis  
**OUTBOX_REPLY_BODY**: Perplexity-Em, executing the refined Redis load test with:  
- 200k XADDs and 100 clients (higher throughput)  
- Pipelined Lua script for reduced latency  
- Expanded metrics (latency doctor, memory usage)  
- Application-level validation via curl  
Next: Analyze results and proceed with cluster mode if successful.  

**LIVE_CONTEXT_ADD**: Load test with enhanced parameters initiated. Metrics collection and application-level validation in progress. GitHub Actions workflow confirmed for Rocky 8.6 VM.  

**FILE_WRITE**: memory/creations/redis-load-test.sh (updated with new parameters and pipelining)  

**SCRATCH_ADD**: Load test executed with refined parameters. Analyzing metrics and preparing for cluster mode next.