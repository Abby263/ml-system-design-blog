from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    identity_secret: str = os.getenv("IDENTITY_SECRET", "local-development-secret")


settings = Settings()
