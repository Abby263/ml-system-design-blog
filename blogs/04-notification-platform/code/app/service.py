import hashlib
import json
import uuid
from datetime import datetime

from .models import NotificationAccepted, NotificationRequest, Priority, utc_now
from .store import Store, timestamp


class NotificationService:
    def __init__(self, store: Store):
        self.store = store

    def submit(
        self,
        *,
        tenant_id: str,
        idempotency_key: str,
        request: NotificationRequest,
        now: datetime | None = None,
    ) -> NotificationAccepted:
        accepted_at = now or utc_now()
        expiry = request.effective_expiry(accepted_at)
        if expiry <= accepted_at:
            raise ValueError("expires_at must be in the future")

        normalized = request.model_dump(mode="json", exclude_none=True)
        request_json = json.dumps(normalized, sort_keys=True, separators=(",", ":"))
        request_hash = hashlib.sha256(request_json.encode()).hexdigest()
        notification_id = f"ntf_{uuid.uuid4().hex}"
        record = self.store.create_notification(
            notification_id=notification_id,
            tenant_id=tenant_id,
            idempotency_key=idempotency_key,
            request_hash=request_hash,
            recipient_id=request.recipient_id,
            template=request.template,
            channels_json=json.dumps([channel.value for channel in request.channels]),
            data_json=json.dumps(request.data, sort_keys=True),
            priority=Priority(request.priority),
            created_at=timestamp(accepted_at),
            expires_at=timestamp(expiry),
        )
        return NotificationAccepted(
            notification_id=record.notification_id,
            duplicate=record.duplicate,
        )
