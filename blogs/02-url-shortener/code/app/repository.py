from datetime import datetime

import asyncpg

from .models import LinkRecord


class AliasAlreadyExists(Exception):
    pass


class LinkRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self.pool = pool

    async def next_id(self) -> int:
        return await self.pool.fetchval("SELECT nextval('url_id_seq')")

    async def create(
        self,
        *,
        link_id: int,
        short_code: str,
        target_url: str,
        expires_at: datetime | None,
    ) -> LinkRecord:
        try:
            row = await self.pool.fetchrow(
                """
                INSERT INTO short_links (id, short_code, target_url, expires_at)
                VALUES ($1, $2, $3, $4)
                RETURNING id, short_code, target_url, created_at, expires_at
                """,
                link_id,
                short_code,
                target_url,
                expires_at,
            )
        except asyncpg.UniqueViolationError as error:
            raise AliasAlreadyExists(short_code) from error
        return LinkRecord.model_validate(dict(row))

    async def get_active(self, short_code: str) -> LinkRecord | None:
        row = await self.pool.fetchrow(
            """
            SELECT id, short_code, target_url, created_at, expires_at
            FROM short_links
            WHERE short_code = $1
              AND deleted_at IS NULL
              AND (expires_at IS NULL OR expires_at > now())
            """,
            short_code,
        )
        return LinkRecord.model_validate(dict(row)) if row else None
