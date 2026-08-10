TOKEN_BUCKET_LUA = r"""
-- KEYS[1] bucket key
-- ARGV: capacity, refill/second, request cost; all scaled by 1000
local capacity = tonumber(ARGV[1])
local refill_per_second = tonumber(ARGV[2])
local cost = tonumber(ARGV[3])

local redis_time = redis.call('TIME')
local now_ms = redis_time[1] * 1000 + math.floor(redis_time[2] / 1000)

local state = redis.call('HMGET', KEYS[1], 'tokens', 'updated_ms')
local tokens = tonumber(state[1]) or capacity
local updated_ms = tonumber(state[2]) or now_ms
local elapsed_ms = math.max(0, now_ms - updated_ms)

local refill = math.floor(elapsed_ms * refill_per_second / 1000)
tokens = math.min(capacity, tokens + refill)

local allowed = 0
if tokens >= cost then
  tokens = tokens - cost
  allowed = 1
end

local deficit = math.max(0, cost - tokens)
local retry_after_ms = math.ceil(deficit * 1000 / refill_per_second)
local reset_after_ms = math.ceil((capacity - tokens) * 1000 / refill_per_second)
local ttl_ms = math.max(1000, math.ceil(capacity * 1000 / refill_per_second) * 2)

redis.call('HSET', KEYS[1], 'tokens', tokens, 'updated_ms', now_ms)
redis.call('PEXPIRE', KEYS[1], ttl_ms)

return {
  allowed,
  math.floor(tokens / 1000),
  retry_after_ms,
  reset_after_ms,
  now_ms
}
"""
