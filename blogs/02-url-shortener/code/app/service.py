from .cache import LinkCache
from .models import CreateLinkRequest, LinkRecord
from .repository import AliasAlreadyExists, LinkRepository
from .short_codes import encode_base62


class LinkService:
    def __init__(self, repository: LinkRepository, cache: LinkCache) -> None:
        self.repository = repository
        self.cache = cache

    async def create(self, request: CreateLinkRequest) -> LinkRecord:
        if request.custom_alias:
            link_id = await self.repository.next_id()
            record = await self.repository.create(
                link_id=link_id,
                short_code=request.custom_alias,
                target_url=request.target_url,
                expires_at=request.expires_at,
            )
            await self.cache.put(record)
            return record

        # A custom alias may already occupy a code the sequence later reaches.
        # Keep one namespace and advance rather than adding a coordination service.
        for _ in range(5):
            link_id = await self.repository.next_id()
            try:
                record = await self.repository.create(
                    link_id=link_id,
                    short_code=encode_base62(link_id),
                    target_url=request.target_url,
                    expires_at=request.expires_at,
                )
            except AliasAlreadyExists:
                continue
            await self.cache.put(record)
            return record
        raise RuntimeError("could not allocate a generated short code")

    async def resolve(self, short_code: str) -> LinkRecord | None:
        cached = await self.cache.get(short_code)
        if cached.hit:
            return cached.record

        record = await self.repository.get_active(short_code)
        if record is None:
            await self.cache.put_missing(short_code)
            return None
        await self.cache.put(record)
        return record
