from dataclasses import dataclass
from enum import StrEnum
from hashlib import sha256
from typing import Protocol

from .models import Channel


class ProviderOutcome(StrEnum):
    ACCEPTED = "accepted"
    RETRYABLE = "retryable"
    TERMINAL_ENDPOINT = "terminal_endpoint"
    TERMINAL_REQUEST = "terminal_request"


@dataclass(frozen=True)
class ProviderRequest:
    delivery_id: str
    channel: Channel
    endpoint: str
    template: str
    data: dict[str, object]
    attempt: int


@dataclass(frozen=True)
class ProviderResult:
    outcome: ProviderOutcome
    provider: str
    provider_message_id: str | None = None
    error: str | None = None
    retry_after_seconds: float | None = None


class ProviderAdapter(Protocol):
    def send(self, request: ProviderRequest) -> ProviderResult: ...


class FakeProviderAdapter:
    """A deterministic provider simulator; no notification leaves the machine."""

    def __init__(self, provider: str):
        self.provider = provider

    def send(self, request: ProviderRequest) -> ProviderResult:
        endpoint = request.endpoint.lower()
        if "invalid" in endpoint:
            return ProviderResult(
                outcome=ProviderOutcome.TERMINAL_ENDPOINT,
                provider=self.provider,
                error="provider rejected an invalid endpoint",
            )
        if "reject" in endpoint:
            return ProviderResult(
                outcome=ProviderOutcome.TERMINAL_REQUEST,
                provider=self.provider,
                error="provider rejected the request payload",
            )
        if "retry" in endpoint and request.attempt == 1:
            return ProviderResult(
                outcome=ProviderOutcome.RETRYABLE,
                provider=self.provider,
                error="simulated provider throttling",
                retry_after_seconds=2.0,
            )
        provider_id = sha256(f"{self.provider}:{request.delivery_id}".encode()).hexdigest()[:24]
        return ProviderResult(
            outcome=ProviderOutcome.ACCEPTED,
            provider=self.provider,
            provider_message_id=f"msg_{provider_id}",
        )


class ProviderFactory:
    def __init__(self) -> None:
        self._providers = {
            Channel.EMAIL: FakeProviderAdapter("fake-email"),
            Channel.SMS: FakeProviderAdapter("fake-sms"),
            Channel.PUSH: FakeProviderAdapter("fake-push"),
        }

    def for_channel(self, channel: Channel) -> ProviderAdapter:
        return self._providers[channel]
