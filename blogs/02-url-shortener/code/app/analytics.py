from datetime import datetime, timezone
import json
import socket

import asyncpg
from redis.asyncio import Redis
from redis.exceptions import ResponseError

from .settings import settings


class AnalyticsPublisher:
    def __init__(self, redis: Redis) -> None:
        self.redis = redis

    async def publish_click(self, short_code: str, user_agent: str | None) -> None:
        """Best effort by design: analytics must never break redirects."""
        event = {
            "short_code": short_code,
            "occurred_at": datetime.now(timezone.utc).isoformat(),
            "user_agent": (user_agent or "")[:256],
        }
        try:
            await self.redis.xadd(
                settings.analytics_stream,
                {"event": json.dumps(event)},
                maxlen=1_000_000,
                approximate=True,
            )
        except Exception:
            pass


async def ensure_consumer_group(redis: Redis) -> None:
    try:
        await redis.xgroup_create(
            settings.analytics_stream,
            settings.analytics_group,
            id="0",
            mkstream=True,
        )
    except ResponseError as error:
        if "BUSYGROUP" not in str(error):
            raise


async def consume_forever(redis: Redis, pool: asyncpg.Pool) -> None:
    await ensure_consumer_group(redis)
    consumer = socket.gethostname()
    while True:
        batches = await redis.xreadgroup(
            settings.analytics_group,
            consumer,
            {settings.analytics_stream: ">"},
            count=250,
            block=2_000,
        )
        for _, messages in batches:
            for message_id, fields in messages:
                event = json.loads(fields["event"])
                await pool.execute(
                    """
                    INSERT INTO daily_clicks (short_code, click_date, clicks)
                    VALUES ($1, $2::timestamptz::date, 1)
                    ON CONFLICT (short_code, click_date)
                    DO UPDATE SET clicks = daily_clicks.clicks + 1
                    """,
                    event["short_code"],
                    event["occurred_at"],
                )
                await redis.xack(settings.analytics_stream, settings.analytics_group, message_id)
