from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field, model_validator


class Action(StrEnum):
    ALLOW = "allow"
    CHALLENGE = "challenge"
    REVIEW = "review"
    BLOCK = "block"


class RiskRequest(BaseModel):
    transaction_id: str = Field(min_length=1, max_length=200)
    event_time: datetime
    account_id: str = Field(min_length=1, max_length=200)
    account_created_at: datetime
    card_token: str = Field(min_length=1, max_length=200)
    device_id: str = Field(min_length=1, max_length=200)
    ip_prefix: str = Field(min_length=1, max_length=200)
    country: str = Field(min_length=2, max_length=2)
    merchant_id: str = Field(min_length=1, max_length=200)
    amount_minor: int = Field(gt=0, le=100_000_000)
    currency: str = Field(min_length=3, max_length=3)
    cvv_result: str = Field(pattern="^(match|fail|unavailable)$")

    @model_validator(mode="after")
    def account_exists_before_payment(self) -> "RiskRequest":
        if self.account_created_at > self.event_time:
            raise ValueError("account_created_at must not be after event_time")
        return self


class RiskDecisionView(BaseModel):
    decision_id: str
    transaction_id: str
    action: Action
    risk_score: float
    reason_codes: list[str]
    features: dict[str, float]
    model_version: str
    feature_version: str
    policy_version: str
    degraded: bool
    unavailable_sources: list[str]
    idempotent_replay: bool = False


class LabelRequest(BaseModel):
    label_type: str = Field(pattern="^(analyst|chargeback|appeal|challenge)$")
    label_value: str = Field(pattern="^(fraud|legitimate|inconclusive)$")
    source: str = Field(min_length=1, max_length=200)
    confidence: float = Field(ge=0.0, le=1.0)
    observed_at: datetime
    correction_of: str | None = None


class LabelView(LabelRequest):
    label_id: str
    decision_id: str
