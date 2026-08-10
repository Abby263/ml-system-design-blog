from dataclasses import dataclass
import math


@dataclass(frozen=True)
class RateLimitPolicy:
    name: str
    capacity: int
    refill_per_second: float
    cost: int = 1
    fail_open: bool = False

    def __post_init__(self) -> None:
        if self.capacity <= 0:
            raise ValueError("capacity must be positive")
        if self.refill_per_second <= 0:
            raise ValueError("refill_per_second must be positive")
        if self.cost <= 0 or self.cost > self.capacity:
            raise ValueError("cost must be between 1 and capacity")

    @property
    def window_seconds(self) -> int:
        return max(1, math.ceil(self.capacity / self.refill_per_second))


@dataclass(frozen=True)
class RateLimitDecision:
    allowed: bool
    remaining: int
    retry_after_ms: int
    reset_after_ms: int
    policy: RateLimitPolicy

    def headers(self) -> dict[str, str]:
        reset_seconds = max(1, math.ceil(self.reset_after_ms / 1000))
        headers = {
            "RateLimit-Policy": (
                f'"{self.policy.name}";q={self.policy.capacity};w={self.policy.window_seconds}'
            ),
            "RateLimit": f'"{self.policy.name}";r={self.remaining};t={reset_seconds}',
        }
        if not self.allowed:
            headers["Retry-After"] = str(max(1, math.ceil(self.retry_after_ms / 1000)))
        return headers
