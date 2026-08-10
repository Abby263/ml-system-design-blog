"""Small, dependency-free capacity calculator for an ML decision system."""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass

SECONDS_PER_DAY = 86_400


@dataclass(frozen=True)
class CapacityInputs:
    daily_decisions: int = 100_000_000
    peak_factor: float = 5.0
    event_kb: float = 3.0
    service_time_ms: float = 40.0
    safe_rps_per_replica: float = 250.0
    replica_headroom: float = 1.0

    def validate(self) -> None:
        values = asdict(self)
        for name, value in values.items():
            if value <= 0:
                raise ValueError(f"{name} must be greater than zero")
        if self.peak_factor < 1:
            raise ValueError("peak_factor must be at least 1")
        if self.replica_headroom < 1:
            raise ValueError("replica_headroom must be at least 1")


@dataclass(frozen=True)
class CapacityEnvelope:
    average_rps: float
    peak_rps: float
    raw_event_gb_per_day: float
    in_flight_requests: float
    replica_floor: int


def estimate(inputs: CapacityInputs) -> CapacityEnvelope:
    """Return a transparent first-pass envelope, not an autoscaling policy."""

    inputs.validate()
    average_rps = inputs.daily_decisions / SECONDS_PER_DAY
    peak_rps = average_rps * inputs.peak_factor
    event_bytes = inputs.event_kb * 1_000
    raw_event_gb_per_day = inputs.daily_decisions * event_bytes / 1_000_000_000
    in_flight_requests = peak_rps * inputs.service_time_ms / 1_000
    replica_floor = math.ceil(
        peak_rps / inputs.safe_rps_per_replica * inputs.replica_headroom
    )
    return CapacityEnvelope(
        average_rps=average_rps,
        peak_rps=peak_rps,
        raw_event_gb_per_day=raw_event_gb_per_day,
        in_flight_requests=in_flight_requests,
        replica_floor=replica_floor,
    )


def validate_latency_budget(target_ms: float, **components_ms: float) -> float:
    """Validate a latency allocation and return its remaining slack."""

    if target_ms <= 0:
        raise ValueError("target_ms must be greater than zero")
    if not components_ms:
        raise ValueError("at least one latency component is required")
    if any(value < 0 for value in components_ms.values()):
        raise ValueError("latency components cannot be negative")
    used_ms = sum(components_ms.values())
    if used_ms > target_ms:
        raise ValueError(
            f"latency budget exceeds target by {used_ms - target_ms:.1f} ms"
        )
    return target_ms - used_ms


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--daily-decisions", type=int, default=100_000_000)
    parser.add_argument("--peak-factor", type=float, default=5.0)
    parser.add_argument("--event-kb", type=float, default=3.0)
    parser.add_argument("--service-time-ms", type=float, default=40.0)
    parser.add_argument("--safe-rps-per-replica", type=float, default=250.0)
    parser.add_argument("--replica-headroom", type=float, default=1.0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    envelope = estimate(
        CapacityInputs(
            daily_decisions=args.daily_decisions,
            peak_factor=args.peak_factor,
            event_kb=args.event_kb,
            service_time_ms=args.service_time_ms,
            safe_rps_per_replica=args.safe_rps_per_replica,
            replica_headroom=args.replica_headroom,
        )
    )
    print(json.dumps(asdict(envelope), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
