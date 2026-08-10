from redis.asyncio import Redis

from .identity import partition_key
from .models import RateLimitDecision, RateLimitPolicy
from .script import TOKEN_BUCKET_LUA


SCALE = 1000


class RedisTokenBucket:
    def __init__(self, redis: Redis) -> None:
        self.redis = redis
        self.script = redis.register_script(TOKEN_BUCKET_LUA)

    async def allow(self, identity: str, policy: RateLimitPolicy) -> RateLimitDecision:
        result = await self.script(
            keys=[partition_key(policy.name, identity)],
            args=[
                policy.capacity * SCALE,
                round(policy.refill_per_second * SCALE),
                policy.cost * SCALE,
            ],
        )
        allowed, remaining, retry_after_ms, reset_after_ms, _ = map(int, result)
        return RateLimitDecision(
            allowed=bool(allowed),
            remaining=remaining,
            retry_after_ms=retry_after_ms,
            reset_after_ms=reset_after_ms,
            policy=policy,
        )
