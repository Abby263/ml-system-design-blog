from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request
from pydantic import BaseModel

from .artifacts import ModelBundle
from .pipeline import RecommendationPipeline
from .settings import settings


class RecommendationView(BaseModel):
    item_id: str
    score: float
    sources: list[str]
    reason: str


class RecommendationResponse(BaseModel):
    model_version: str
    degraded: bool
    failed_sources: list[str]
    recommendations: list[RecommendationView]


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not Path(settings.artifact_path).exists():
        raise RuntimeError(
            f"artifact not found at {settings.artifact_path}; run recommendation-train first"
        )
    app.state.pipeline = RecommendationPipeline(ModelBundle.load(settings.artifact_path))
    yield


app = FastAPI(title="Designing ML Systems Recommendation Service", lifespan=lifespan)


@app.get("/healthz")
async def health(request: Request) -> dict[str, str]:
    pipeline: RecommendationPipeline = request.app.state.pipeline
    return {"status": "ok", "model_version": pipeline.bundle.version}


@app.get("/v1/recommendations", response_model=RecommendationResponse)
async def recommendations(
    request: Request,
    user_id: str = Query(min_length=1, max_length=200),
    limit: int = Query(default=20, ge=1, le=50),
    session_items: str = "",
    fail_sources: str = "",
) -> RecommendationResponse:
    pipeline: RecommendationPipeline = request.app.state.pipeline
    requested_failures = {source for source in fail_sources.split(",") if source}
    allowed = {"embedding", "co_watch", "popular", "fresh"}
    unknown = requested_failures - allowed
    if unknown:
        raise HTTPException(status_code=422, detail=f"unknown sources: {sorted(unknown)}")
    result = pipeline.recommend(
        user_id=user_id,
        limit=limit,
        session_items=[item for item in session_items.split(",") if item],
        fail_sources=requested_failures,
    )
    return RecommendationResponse.model_validate(result, from_attributes=True)
