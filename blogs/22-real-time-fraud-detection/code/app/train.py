import argparse
import csv
from pathlib import Path

import numpy as np

from .artifacts import FEATURE_NAMES, ModelBundle, artifact_version
from .settings import settings


def read_rows(path: str) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return sorted(csv.DictReader(handle), key=lambda row: row["event_time"])


def matrix(rows: list[dict[str, str]]) -> tuple[np.ndarray, np.ndarray]:
    features = np.asarray(
        [[float(row[name]) for name in FEATURE_NAMES] for row in rows],
        dtype=np.float64,
    )
    labels = np.asarray([float(row["label"]) for row in rows], dtype=np.float64)
    return features, labels


def fit_bundle(
    rows: list[dict[str, str]], epochs: int = 2_000, learning_rate: float = 0.04
) -> ModelBundle:
    if len(rows) < 4 or len({row["label"] for row in rows}) < 2:
        raise ValueError("training requires at least four rows and both labels")
    values, labels = matrix(rows)
    means = values.mean(axis=0)
    scales = values.std(axis=0)
    scales = np.where(scales < 1e-9, 1.0, scales)
    normalized = (values - means) / scales
    weights = np.zeros(normalized.shape[1], dtype=np.float64)
    bias = 0.0
    positive_weight = max(1.0, float((labels == 0).sum() / max(1, (labels == 1).sum())))
    sample_weights = np.where(labels == 1, positive_weight, 1.0)

    for _ in range(epochs):
        logits = np.clip(normalized @ weights + bias, -30.0, 30.0)
        predictions = 1.0 / (1.0 + np.exp(-logits))
        error = (predictions - labels) * sample_weights
        weights -= learning_rate * (normalized.T @ error / sample_weights.sum())
        bias -= learning_rate * float(error.sum() / sample_weights.sum())

    payload = {
        "trained_through": rows[-1]["event_time"],
        "feature_names": FEATURE_NAMES,
        "means": means.round(10).tolist(),
        "scales": scales.round(10).tolist(),
        "weights": weights.round(10).tolist(),
        "bias": round(bias, 10),
    }
    return ModelBundle(version=artifact_version(payload), **payload)


def main() -> None:
    parser = argparse.ArgumentParser(description="Train a temporal class-weighted fraud baseline")
    parser.add_argument("--data", default=settings.training_data_path)
    parser.add_argument("--output", default=settings.artifact_path)
    parser.add_argument("--train-fraction", type=float, default=0.7)
    arguments = parser.parse_args()
    rows = read_rows(arguments.data)
    cutoff = max(4, min(len(rows) - 1, int(len(rows) * arguments.train_fraction)))
    bundle = fit_bundle(rows[:cutoff])
    bundle.save(arguments.output)
    print(
        f"wrote model {bundle.version} trained_through={bundle.trained_through} "
        f"rows={cutoff} to {arguments.output}"
    )


if __name__ == "__main__":
    main()
