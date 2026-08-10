from dataclasses import dataclass
from datetime import datetime, timezone
import json

from redis.asyncio import Redis

from .models import LinkRecord
from .settings import settings


@dataclass(frozen=True)
class CacheLookup:
    hit: bool
    record: LinkRecord | None


class LinkCache:
    def __init__(self, redis: Redis) -> None:
        self.redis = redis

    @staticmethod
    def key(short_code: str) -> str:
        return f"short-link:v1:{short_code}"

    async def get(self, short_code: str) -> CacheLookup:
        try:
            value = await self.redis.get(self.key(short_code))
        except Exception:
            return CacheLookup(hit=False, record=None)
        if value is None:
            return CacheLookup(hit=False, record=None)
        try:
            payload = json.loads(value)
            if payload.get("missing"):
                return CacheLookup(hit=True, record=None)
            record = LinkRecord.model_validate_json(value)
        except Exception:
            try:
                await self.redis.delete(self.key(short_code))
            except Exception:
                pass
            return CacheLookup(hit=False, record=None)
        if record.expires_at and record.expires_at <= datetime.now(timezone.utc):
            try:
                await self.redis.delete(self.key(short_code))
            except Exception:
                pass
            return CacheLookup(hit=True, record=None)
        return CacheLookup(hit=True, record=record)

    async def put(self, record: LinkRecord) -> None:
        ttl = settings.cache_ttl_seconds
        if record.expires_at:
            remaining = int((record.expires_at - datetime.now(timezone.utc)).total_seconds())
            if remaining <= 0:
                return
            ttl = min(ttl, remaining)
        try:
            await self.redis.set(
                self.key(record.short_code),
                record.model_dump_json(),
                ex=ttl,
            )
        except Exception:
            pass

    async def put_missing(self, short_code: str) -> None:
        try:
            await self.redis.set(
                self.key(short_code),
                json.dumps({"missing": True}),
                ex=settings.negative_cache_ttl_seconds,
            )
        except Exception:
            pass
