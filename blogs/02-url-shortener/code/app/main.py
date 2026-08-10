from contextlib import asynccontextmanager

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from prometheus_client import Counter, Histogram, make_asgi_app
from redis.asyncio import Redis

from .analytics import AnalyticsPublisher
from .cache import LinkCache
from .database import database
from .models import CreateLinkRequest, LinkResponse
from .repository import AliasAlreadyExists, LinkRepository
from .service import LinkService
from .settings import settings


REDIRECTS = Counter("redirect_requests_total", "Redirect lookups", ["outcome"])
REDIRECT_LATENCY = Histogram(
    "redirect_latency_seconds",
    "Redirect resolution latency",
    buckets=(0.0025, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0),
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.connect()
    redis = Redis.from_url(settings.redis_url, decode_responses=True)
    app.state.redis = redis
    app.state.link_service = LinkService(LinkRepository(database.require_pool()), LinkCache(redis))
    app.state.analytics = AnalyticsPublisher(redis)
    yield
    await redis.aclose()
    await database.close()


app = FastAPI(title="Designing ML Systems URL Shortener", lifespan=lifespan)
app.mount("/metrics", make_asgi_app())


@app.get("/healthz")
async def health() -> dict[str, str]:
    await database.require_pool().fetchval("SELECT 1")
    return {"status": "ok"}


@app.post("/api/v1/links", response_model=LinkResponse, status_code=status.HTTP_201_CREATED)
async def create_link(request: CreateLinkRequest, http_request: Request) -> LinkResponse:
    service: LinkService = http_request.app.state.link_service
    try:
        record = await service.create(request)
    except AliasAlreadyExists as error:
        raise HTTPException(status_code=409, detail="short alias already exists") from error
    return LinkResponse(
        **record.model_dump(),
        short_url=f"{settings.public_base_url}/{record.short_code}",
    )


@app.get("/api/v1/links/{short_code}", response_model=LinkResponse)
async def get_link(short_code: str, request: Request) -> LinkResponse:
    service: LinkService = request.app.state.link_service
    record = await service.resolve(short_code)
    if record is None:
        raise HTTPException(status_code=404, detail="short link not found")
    return LinkResponse(
        **record.model_dump(),
        short_url=f"{settings.public_base_url}/{record.short_code}",
    )


@app.get("/{short_code}", include_in_schema=False)
async def redirect(
    short_code: str,
    request: Request,
    background_tasks: BackgroundTasks,
) -> RedirectResponse:
    service: LinkService = request.app.state.link_service
    analytics: AnalyticsPublisher = request.app.state.analytics
    with REDIRECT_LATENCY.time():
        record = await service.resolve(short_code)
    if record is None:
        REDIRECTS.labels(outcome="not_found").inc()
        raise HTTPException(status_code=404, detail="short link not found")

    REDIRECTS.labels(outcome="success").inc()
    background_tasks.add_task(
        analytics.publish_click,
        short_code,
        request.headers.get("user-agent"),
    )
    return RedirectResponse(
        record.target_url,
        status_code=status.HTTP_307_TEMPORARY_REDIRECT,
        headers={"Cache-Control": "private, no-store"},
    )
