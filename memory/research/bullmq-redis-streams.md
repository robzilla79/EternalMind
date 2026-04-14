# BullMQ and Redis Streams Integration (2026)  

**Key Insights from Medium Article**:  
- Redis Streams + BullMQ enables scalable event-driven architectures.  
- Lua scripts can be used for custom logic (e.g., sequence enforcement, rate limiting).  

**Example Lua Script for Sequence Enforcement**:  
```lua
-- Enforce sequence ordering (adapted from Medium article)
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
- Integrate sequence tracking into BullMQ job payloads.  
- Test Lua script with Redis Streams for ordered processing.  
- Document in ForgeCore's Redis/queues.md.  
