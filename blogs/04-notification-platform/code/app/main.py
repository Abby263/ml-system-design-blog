import hashlib
import hmac
import json
from contextlib import asynccontextmanager
from datetime import UTC, datetime

from fastapi import FastAPI, Header, HTTPException, Request, Response, status

from .models import (
    DeliveryState,
    DeliveryView,
    NotificationAccepted,
    NotificationRequest,
    NotificationView,
    Priority,
    ProviderCallback,
)
from .service import NotificationService
from .settings import settings
from .store import IdempotencyConflict, Store


store = Store(settings.database_path)
service = NotificationService(store)


@asynccontextmanager
async def lifespan(_: FastAPI):
    store.initialize()
    yield


app = FastAPI(title="Designing ML Systems Notification Platform", lifespan=lifespan)


@app.get("/healthz")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post(
    "/v1/notifications",
    response_model=NotificationAccepted,
    status_code=status.HTTP_202_ACCEPTED,
)
async def submit_notification(
    payload: NotificationRequest,
    response: Response,
    x_tenant_id: str = Header(default="demo"),
    idempotency_key: str = Header(min_length=1, max_length=200),
) -> NotificationAccepted:
    try:
        accepted = service.submit(
            tenant_id=x_tenant_id,
            idempotency_key=idempotency_key,
            request=payload,
        )
    except IdempotencyConflict as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)
        ) from error
    response.headers["Location"] = f"/v1/notifications/{accepted.notification_id}"
    return accepted


@app.get("/v1/notifications/{notification_id}", response_model=NotificationView)
async def notification_status(notification_id: str) -> NotificationView:
    result = store.notification(notification_id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="notification not found")
    notification, deliveries = result
    return NotificationView(
        id=notification["id"],
        tenant_id=notification["tenant_id"],
        recipient_id=notification["recipient_id"],
        template=notification["template"],
        priority=Priority(notification["priority"]),
        created_at=datetime.fromtimestamp(notification["created_at"], tz=UTC),
        expires_at=datetime.fromtimestamp(notification["expires_at"], tz=UTC),
        deliveries=[
            DeliveryView(
                id=row["id"],
                channel=row["channel"],
                endpoint=row["endpoint"],
                state=DeliveryState(row["state"]),
                attempts=row["attempts"],
                provider=row["provider"],
                provider_message_id=row["provider_message_id"],
                last_error=row["last_error"],
            )
            for row in deliveries
        ],
    )


@app.post("/v1/provider-callbacks/{provider}")
async def provider_callback(
    provider: str,
    request: Request,
    x_provider_signature: str = Header(),
) -> dict[str, bool]:
    raw_body = await request.body()
    expected = hmac.new(settings.callback_secret.encode(), raw_body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, x_provider_signature):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid signature")
    try:
        payload = ProviderCallback.model_validate_json(raw_body)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)
        ) from error
    try:
        inserted = store.apply_provider_event(
            provider=provider,
            event_id=payload.event_id,
            delivery_id=payload.delivery_id,
            incoming=payload.status,
            raw_json=json.dumps(payload.model_dump(mode="json"), sort_keys=True),
            now=datetime.now(UTC).timestamp(),
        )
    except KeyError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="delivery not found; event should be quarantined",
        ) from error
    return {"accepted": inserted}
