from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv(
        "DATABASE_URL", "postgresql://shortener:shortener@localhost:5432/shortener"
    )
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    public_base_url: str = os.getenv("PUBLIC_BASE_URL", "http://localhost:8000")
    cache_ttl_seconds: int = int(os.getenv("CACHE_TTL_SECONDS", "300"))
    negative_cache_ttl_seconds: int = int(os.getenv("NEGATIVE_CACHE_TTL_SECONDS", "15"))
    analytics_stream: str = os.getenv("ANALYTICS_STREAM", "click-events")
    analytics_group: str = os.getenv("ANALYTICS_GROUP", "analytics-workers")


settings = Settings()
