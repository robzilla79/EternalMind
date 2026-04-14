-- Pre-population Lua script (100k entries with 500ms idle time)  
local stream_key = "stress_test_stream"  
local group_name = "stress_group"  
local consumer_name = "prepopulator"  

redis.call("XGROUP", "CREATE", stream_key, group_name, "0-0", "MKSTREAM")  

for i=1,100000 do  
    local id = redis.call("XADD", stream_key, "MAXLEN", "~ 100000", "RETENTION", "~ 86400",  
        "*", "payload", "test_data", "idle_time", 500)  
    redis.call("XCLAIM", stream_key, group_name, consumer_name, "JUSTID", "IDLE", 500, "TIME", id)  
end  
