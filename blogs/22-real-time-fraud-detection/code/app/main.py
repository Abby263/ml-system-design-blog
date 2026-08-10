from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException, Query, Request

from .artifacts import ModelBundle
from .models import LabelRequest, LabelView, RiskDecisionView, RiskRequest
from .service import RiskService
from .settings import settings
from .store import DecisionNotFound, IdempotencyConflict, Store


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not Path(settings.artifact_path).exists():
        raise RuntimeError(f"model missing at {settings.artifact_path}; run fraud-train first")
    store = Store(settings.database_path)
    app.state.store = store
    app.state.risk = RiskService(store, ModelBundle.load(settings.artifact_path))
    yield


app = FastAPI(title="Designing ML Systems Fraud Decision Service", lifespan=lifespan)


@app.get("/healthz")
async def health(request: Request) -> dict[str, str]:
    service: RiskService = request.app.state.risk
    return {"status": "ok", "model_version": service.model.version}


@app.post("/v1/risk-decisions", response_model=RiskDecisionView)
async def risk_decision(
    payload: RiskRequest,
    request: Request,
    idempotency_key: str = Header(min_length=1, max_length=200),
    fail_model: bool = Query(default=False),
    stale_features: bool = Query(default=False),
) -> RiskDecisionView:
    service: RiskService = request.app.state.risk
    try:
        return service.decide(
            idempotency_key=idempotency_key,
            request=payload,
            fail_model=fail_model,
            stale_features=stale_features,
        )
    except IdempotencyConflict as error:
        raise HTTPException(
            status_code=409, detail="idempotency key reused with another body"
        ) from error


@app.post("/v1/risk-decisions/{decision_id}/labels", response_model=LabelView, status_code=201)
async def add_label(decision_id: str, payload: LabelRequest, request: Request) -> LabelView:
    store: Store = request.app.state.store
    try:
        return store.add_label(decision_id, payload)
    except DecisionNotFound as error:
        raise HTTPException(
            status_code=404, detail="decision or correction label not found"
        ) from error
