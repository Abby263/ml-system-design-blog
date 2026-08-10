import asyncpg

from .settings import settings


class Database:
    def __init__(self) -> None:
        self.pool: asyncpg.Pool | None = None

    async def connect(self) -> None:
        self.pool = await asyncpg.create_pool(
            settings.database_url,
            min_size=2,
            max_size=20,
            command_timeout=2,
        )

    async def close(self) -> None:
        if self.pool is not None:
            await self.pool.close()

    def require_pool(self) -> asyncpg.Pool:
        if self.pool is None:
            raise RuntimeError("database is not connected")
        return self.pool


database = Database()
