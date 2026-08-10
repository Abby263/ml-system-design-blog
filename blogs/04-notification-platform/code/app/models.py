from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class Channel(StrEnum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"


class Priority(StrEnum):
    TRANSACTIONAL = "transactional"
    NORMAL = "normal"
    BULK = "bulk"


class DeliveryState(StrEnum):
    QUEUED = "queued"
    LEASED = "leased"
    SENDING = "sending"
    RETRY_SCHEDULED = "retry_scheduled"
    PROVIDER_ACCEPTED = "provider_accepted"
    DELIVERED = "delivered"
    READ = "read"
    SUPPRESSED = "suppressed"
    EXPIRED = "expired"
    FAILED = "failed"


class NotificationRequest(BaseModel):
    recipient_id: str = Field(min_length=1, max_length=200)
    template: str = Field(min_length=1, max_length=100)
    channels: list[Channel] = Field(min_length=1, max_length=3)
    data: dict[str, Any] = Field(default_factory=dict)
    priority: Priority = Priority.NORMAL
    expires_at: datetime | None = None

    @field_validator("channels")
    @classmethod
    def channels_are_unique(cls, channels: list[Channel]) -> list[Channel]:
        if len(channels) != len(set(channels)):
            raise ValueError("channels must be unique")
        return channels

    @field_validator("expires_at")
    @classmethod
    def expiry_has_timezone(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError("expires_at must include a timezone")
        return value

    def effective_expiry(self, now: datetime) -> datetime:
        return self.expires_at or now + timedelta(hours=1)


class NotificationAccepted(BaseModel):
    notification_id: str
    status: str = "accepted"
    duplicate: bool = False


class ProviderCallback(BaseModel):
    event_id: str = Field(min_length=1, max_length=200)
    delivery_id: str = Field(min_length=1, max_length=200)
    status: DeliveryState
    provider_message_id: str | None = None

    @field_validator("status")
    @classmethod
    def callback_status_is_external(cls, status: DeliveryState) -> DeliveryState:
        allowed = {DeliveryState.DELIVERED, DeliveryState.READ, DeliveryState.FAILED}
        if status not in allowed:
            raise ValueError("callback status must be delivered, read, or failed")
        return status


class DeliveryView(BaseModel):
    id: str
    channel: Channel
    endpoint: str
    state: DeliveryState
    attempts: int
    provider: str | None
    provider_message_id: str | None
    last_error: str | None


class NotificationView(BaseModel):
    id: str
    tenant_id: str
    recipient_id: str
    template: str
    priority: Priority
    created_at: datetime
    expires_at: datetime
    deliveries: list[DeliveryView]


def utc_now() -> datetime:
    return datetime.now(UTC)
