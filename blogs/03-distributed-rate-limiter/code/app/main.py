from contextlib import asynccontextmanager
from time import perf_counter

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from prometheus_client import Counter, Histogram, make_asgi_app
from redis.asyncio import Redis

from .limiter import RedisTokenBucket
from .models import RateLimitPolicy
from .settings import settings


PUBLIC_READ = RateLimitPolicy(name="public-read", capacity=20, refill_per_second=5, fail_open=True)
EXPENSIVE_REPORT = RateLimitPolicy(
    name="expensive-report", capacity=3, refill_per_second=0.2, fail_open=False
)

DECISIONS = Counter("rate_limit_decisions_total", "Rate-limit decisions", ["policy", "outcome"])
CHECK_LATENCY = Histogram(
    "rate_limit_check_seconds",
    "Redis rate-limit decision latency",
    ["policy"],
    buckets=(0.0005, 0.001, 0.0025, 0.005, 0.01, 0.025, 0.05, 0.1),
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    redis = Redis.from_url(settings.redis_url, decode_responses=True)
    app.state.redis = redis
    app.state.limiter = RedisTokenBucket(redis)
    yield
    await redis.aclose()


app = FastAPI(title="Designing ML Systems Rate Limiter", lifespan=lifespan)
app.mount("/metrics", make_asgi_app())


def request_identity(request: Request) -> str:
    api_key = request.headers.get("x-api-key")
    if api_key:
        return f"api-key:{api_key}"
    forwarded = request.headers.get("x-forwarded-for", "").split(",", 1)[0].strip()
    client_ip = forwarded or (request.client.host if request.client else "unknown")
    return f"ip:{client_ip}"


def enforce(policy: RateLimitPolicy):
    async def dependency(request: Request, response: Response) -> None:
        limiter: RedisTokenBucket = request.app.state.limiter
        started = perf_counter()
        try:
            decision = await limiter.allow(request_identity(request), policy)
        except Exception as error:
            DECISIONS.labels(policy=policy.name, outcome="error").inc()
            if policy.fail_open:
                response.headers["RateLimit-Status"] = "unavailable; decision=allowed"
                return
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="rate-limit authority unavailable",
                headers={"Retry-After": "1"},
            ) from error
        finally:
            CHECK_LATENCY.labels(policy=policy.name).observe(perf_counter() - started)

        for name, value in decision.headers().items():
            response.headers[name] = value
        if not decision.allowed:
            DECISIONS.labels(policy=policy.name, outcome="denied").inc()
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="rate limit exceeded",
                headers=decision.headers(),
            )
        DECISIONS.labels(policy=policy.name, outcome="allowed").inc()

    return dependency


@app.get("/healthz")
async def health(request: Request) -> dict[str, str]:
    await request.app.state.redis.ping()
    return {"status": "ok"}


@app.get("/public-data", dependencies=[Depends(enforce(PUBLIC_READ))])
async def public_data() -> dict[str, str]:
    return {"message": "served with a fail-open limiter"}


@app.post("/expensive-report", dependencies=[Depends(enforce(EXPENSIVE_REPORT))])
async def expensive_report() -> dict[str, str]:
    return {"message": "expensive work accepted"}
