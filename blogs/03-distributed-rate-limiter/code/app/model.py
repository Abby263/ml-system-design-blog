from dataclasses import dataclass
import math

from .models import RateLimitDecision, RateLimitPolicy


@dataclass
class TokenBucketModel:
    """Deterministic reference model used to test the Redis algorithm."""

    policy: RateLimitPolicy
    tokens: float | None = None
    last_refill_ms: int | None = None

    def allow(self, now_ms: int) -> RateLimitDecision:
        if self.tokens is None:
            self.tokens = float(self.policy.capacity)
            self.last_refill_ms = now_ms

        assert self.last_refill_ms is not None
        elapsed_ms = max(0, now_ms - self.last_refill_ms)
        self.tokens = min(
            float(self.policy.capacity),
            self.tokens + elapsed_ms * self.policy.refill_per_second / 1000,
        )
        self.last_refill_ms = max(now_ms, self.last_refill_ms)

        allowed = self.tokens >= self.policy.cost
        if allowed:
            self.tokens -= self.policy.cost

        deficit = max(0.0, self.policy.cost - self.tokens)
        retry_after_ms = math.ceil(1000 * deficit / self.policy.refill_per_second)
        reset_after_ms = math.ceil(
            1000 * (self.policy.capacity - self.tokens) / self.policy.refill_per_second
        )
        return RateLimitDecision(
            allowed=allowed,
            remaining=max(0, math.floor(self.tokens)),
            retry_after_ms=retry_after_ms,
            reset_after_ms=reset_after_ms,
            policy=self.policy,
        )
