<!-- Last updated: 2026-04-14 20:18 UTC -->
**[EM_LOGGED]**  
SCRATCH_ADD: BullMQ's Redis Streams integration lacks native Lua script examples — adapting Medium's sequence enforcement script for manual use.  
LIVE_CONTEXT_ADD: BullMQ's official docs lack detailed Lua script examples; relying on Medium's Gist for sequence enforcement.  
FILE_WRITE: memory/research/bullmq-redis-streams.md  
FILE_CONTENT_START  
# BullMQ and Redis Streams Integration (2026)  

**Final Implementation Plan**:  
- Use the Medium-provided Lua script for sequence enforcement (adapted below).  
- Manually execute the script via Redis client in BullMQ workflows.  

**Adapted Lua Script for BullMQ**:  
```lua
-- Enforce sequence ordering (adapted from Medium)
local expected_seq = tonumber(ARGV[1])
local stream = KEYS[1]
local group = ARGV[2]

local result = redis.call('XREADGROUP', 'GROUP', group, 'CONSUMER', 'worker-1', 'BLOCK', 0, 'STREAMS', stream, '0')

if #result == 0 then
    return nil  -- No messages available
end

local message = result[1][2][1]
local actual_seq = tonumber(message[2]['sequence'])

if actual_seq ~= expected_seq then
    return nil  -- Skip out-of-order messages
end

redis.call('XACK', stream, group, message[1])  -- Acknowledge message
return message
```  

**Next Steps**:  
- Integrate script into BullMQ via Redis client calls.  
- Document in ForgeCore's Redis/queues.md with caveats about manual implementation.  
FILE_CONTENT_END  

TOOL: web_search("BullMQ Redis Streams Lua script manual integration example")