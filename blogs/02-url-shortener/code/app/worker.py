import asyncio

from redis.asyncio import Redis

from .analytics import consume_forever
from .database import database
from .settings import settings


async def main() -> None:
    await database.connect()
    redis = Redis.from_url(settings.redis_url, decode_responses=True)
    try:
        await consume_forever(redis, database.require_pool())
    finally:
        await redis.aclose()
        await database.close()


if __name__ == "__main__":
    asyncio.run(main())
