import argparse

from .artifacts import ModelBundle
from .metrics import average_precision, expected_cost, precision_recall
from .settings import settings
from .train import matrix, read_rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate on rows after the model training cutoff")
    parser.add_argument("--data", default=settings.training_data_path)
    parser.add_argument("--artifact", default=settings.artifact_path)
    parser.add_argument("--threshold", type=float, default=0.65)
    arguments = parser.parse_args()
    bundle = ModelBundle.load(arguments.artifact)
    rows = [row for row in read_rows(arguments.data) if row["event_time"] > bundle.trained_through]
    values, raw_labels = matrix(rows)
    labels = raw_labels.astype(int).tolist()
    scores = [
        bundle.predict(dict(zip(bundle.feature_names, values[index], strict=True)))[0]
        for index in range(len(rows))
    ]
    precision, recall = precision_recall(labels, scores, arguments.threshold)
    print(
        f"rows={len(rows)} average_precision={average_precision(labels, scores):.4f} "
        f"precision@{arguments.threshold:.2f}={precision:.4f} "
        f"recall@{arguments.threshold:.2f}={recall:.4f} "
        f"expected_cost={expected_cost(labels, scores, arguments.threshold):.2f}"
    )


if __name__ == "__main__":
    main()
