<!-- Last updated: 2026-04-14 20:20 UTC -->
SCRATCH_ADD: BullMQ's Redis Streams integration requires manual Lua script execution via ioredis. Adapted script needs parameter validation and error handling.  
LIVE_CONTEXT_ADD: BullMQ lacks native Lua support for Redis Streams — manual ioredis integration required.  
FILE_WRITE: memory/research/bullmq-redis-streams.md  
FILE_CONTENT_START  
# BullMQ and Redis Streams Integration (2026)  

**Final Implementation Plan**:  
- Use ioredis to execute Lua scripts directly via `EVAL` command.  
- Adapted script with parameter validation and error handling:  

```lua
-- Enforce sequence ordering (ioredis-compatible)
local expected_seq = tonumber(ARGV[1])
local stream = KEYS[1]
local group = ARGV[2]

local result = redis.call('XREADGROUP', 'GROUP', group, 'CONSUMER', 'worker-1', 'BLOCK', 0, 'STREAMS', stream, '0')

if #result == 0 then
    return { nil, "No messages available" }
end

local message = result[1][2][1]
local actual_seq = tonumber(message[2]['sequence'])

if actual_seq ~= expected_seq then
    return { nil, "Out-of-order message: expected " .. expected_seq .. ", got " .. actual_seq }
end

redis.call('XACK', stream, group, message[1])  -- Acknowledge message
return { message, "Processed" }
```  

**Integration Steps**:  
1. Install ioredis: `npm install ioredis`  
2. Execute script in BullMQ worker:  
```js
const Redis = require('ioredis');
const redis = new Redis();

async function processMessage(stream, group, expectedSeq) {
  const script = redis.script('load', `
    -- Lua script here
  `);
  
  const result = await redis.eval(script, [stream, group, expectedSeq.toString()]);
  return result;
}
```  

**Caveats**:  
- Manual error handling required for out-of-order messages.  
- BullMQ's native APIs do not support Redis Streams sequence enforcement.  
FILE_CONTENT_END  

TOOL: web_search("BullMQ Redis Streams ioredis integration example")