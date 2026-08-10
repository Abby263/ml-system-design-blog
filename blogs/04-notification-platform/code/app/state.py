import random

from .models import DeliveryState


TERMINAL_STATES = {
    DeliveryState.READ,
    DeliveryState.SUPPRESSED,
    DeliveryState.EXPIRED,
    DeliveryState.FAILED,
}

CALLBACK_PRECEDENCE = {
    DeliveryState.QUEUED: 0,
    DeliveryState.LEASED: 1,
    DeliveryState.SENDING: 2,
    DeliveryState.RETRY_SCHEDULED: 2,
    DeliveryState.PROVIDER_ACCEPTED: 3,
    DeliveryState.FAILED: 4,
    DeliveryState.DELIVERED: 5,
    DeliveryState.READ: 6,
    DeliveryState.SUPPRESSED: 7,
    DeliveryState.EXPIRED: 7,
}


def should_apply_callback(current: DeliveryState, incoming: DeliveryState) -> bool:
    if current in {DeliveryState.SUPPRESSED, DeliveryState.EXPIRED}:
        return False
    if current == DeliveryState.FAILED and incoming not in {
        DeliveryState.DELIVERED,
        DeliveryState.READ,
    }:
        return False
    return CALLBACK_PRECEDENCE[incoming] > CALLBACK_PRECEDENCE[current]


def full_jitter_delay(
    attempt: int,
    base_seconds: float,
    max_seconds: float,
    random_value: float | None = None,
) -> float:
    cap = min(max_seconds, base_seconds * (2 ** max(0, attempt - 1)))
    value = random.random() if random_value is None else random_value
    return max(0.0, min(1.0, value)) * cap
