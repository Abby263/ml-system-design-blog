from datetime import datetime, timezone

from pydantic import BaseModel, Field, field_validator

from .short_codes import normalize_target_url, validate_custom_alias


class CreateLinkRequest(BaseModel):
    target_url: str = Field(max_length=2048)
    custom_alias: str | None = None
    expires_at: datetime | None = None

    @field_validator("target_url")
    @classmethod
    def validate_target_url(cls, value: str) -> str:
        try:
            return normalize_target_url(value)
        except ValueError as error:
            raise ValueError(str(error)) from error

    @field_validator("custom_alias")
    @classmethod
    def validate_alias(cls, value: str | None) -> str | None:
        if value is None:
            return None
        try:
            return validate_custom_alias(value)
        except ValueError as error:
            raise ValueError(str(error)) from error

    @field_validator("expires_at")
    @classmethod
    def validate_expiry(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        normalized = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        if normalized <= datetime.now(timezone.utc):
            raise ValueError("expires_at must be in the future")
        return normalized


class LinkRecord(BaseModel):
    id: int
    short_code: str
    target_url: str
    created_at: datetime
    expires_at: datetime | None = None


class LinkResponse(LinkRecord):
    short_url: str
