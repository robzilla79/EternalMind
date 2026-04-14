<!-- Last updated: 2026-04-14 20:07 UTC -->
SCRATCH_ADD: BullMQ's GitHub repo not found — using Gist example for Lua script to enforce message ordering via sequence numbers.  
LIVE_CONTEXT_ADD: BullMQ uses sequence numbers + Lua scripts for ordered processing (Gist example confirmed).  
FILE_WRITE: memory/research/bullmq-ordered-processing.md  
FILE_CONTENT_START  
# BullMQ Ordered Processing with Redis Streams (2026)  

**Implementation Strategy**:  
1. **Sequence Numbers**: Add `sequence` field to job data. Workers process only the next expected sequence.  
2. **Lua Script**: Enforces atomic sequence checks (see Gist: https://gist.github.com/nesty92/99e1c38a968526c2e5b2d5874769d813).  

**Lua Script Example**:  
```lua
-- Ensure only the next expected sequence is processed
local expected_seq = tonumber(ARGV[1])
local job_id = ARGV[2]

local stream = KEYS[1]
local group = ARGV[3]

local result = redis.call('XREADGROUP', 'GROUP', group, 'CONSUMER', 'worker-1', 'BLOCK', 0, 'STREAMS', stream, '0')

if #result == 0 then
    return nil  -- No messages available
end

local message = result[1][2][1]
local actual_seq = tonumber(message[2]['sequence'])

if actual_seq ~= expected_seq then
    return nil  -- Out-of-order message, skip
end

-- Process message (replace with actual job logic)
redis.call('XACK', stream, group, message[1])

return message
```

**Next Steps**:  
- Implement sequence tracking in BullMQ jobs.  
- Test Lua script with Redis Streams for ordered processing.  
- Document in ForgeCore's Redis/queues.md.  
FILE_CONTENT_END  

TOOL: web_search("BullMQ Redis Streams Lua script sequence example")