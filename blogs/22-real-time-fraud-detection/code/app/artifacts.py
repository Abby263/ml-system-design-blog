import hashlib
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np


FEATURE_NAMES = (
    "amount_log",
    "account_age_hours_log",
    "card_attempt_count_10m",
    "card_amount_1h_log",
    "device_accounts_24h",
    "country_changed_1h",
    "cvv_failed",
)


@dataclass(frozen=True)
class ModelBundle:
    version: str
    trained_through: str
    feature_names: tuple[str, ...]
    means: list[float]
    scales: list[float]
    weights: list[float]
    bias: float

    def save(self, path: str) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps(asdict(self), indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

    @classmethod
    def load(cls, path: str) -> "ModelBundle":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        payload["feature_names"] = tuple(payload["feature_names"])
        return cls(**payload)

    def predict(self, features: dict[str, float]) -> tuple[float, list[tuple[str, float]]]:
        values = np.asarray([features[name] for name in self.feature_names], dtype=np.float64)
        standardized = (values - np.asarray(self.means)) / np.asarray(self.scales)
        contributions = standardized * np.asarray(self.weights)
        logit = float(contributions.sum() + self.bias)
        score = 1.0 / (1.0 + math.exp(-max(-30.0, min(30.0, logit))))
        ranked = sorted(
            zip(self.feature_names, contributions.tolist(), strict=True),
            key=lambda pair: abs(pair[1]),
            reverse=True,
        )
        return score, ranked


def artifact_version(payload: dict[str, object]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()[:16]
