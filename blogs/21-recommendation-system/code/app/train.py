import argparse
import csv
from collections import defaultdict
from dataclasses import asdict
from pathlib import Path

import numpy as np

from .artifacts import Item, ModelBundle, bundle_version
from .settings import settings


EVENT_WEIGHT = {"watch": 1.0, "like": 2.0, "share": 3.0, "hide": -2.0}


def read_items(path: str) -> list[Item]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return [
            Item(
                item_id=row["item_id"],
                creator_id=row["creator_id"],
                topic=row["topic"],
                created_at=row["created_at"],
                quality=float(row["quality"]),
            )
            for row in csv.DictReader(handle)
        ]


def read_interactions(path: str) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def interaction_weight(row: dict[str, str]) -> float:
    event_weight = EVENT_WEIGHT.get(row["event_type"], 0.0)
    watch_fraction = float(row.get("watch_fraction") or 0.0)
    return event_weight * max(0.25, watch_fraction)


def normalize_rows(matrix: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    return matrix / np.where(norms == 0, 1.0, norms)


def build_bundle(
    items: list[Item], interactions: list[dict[str, str]], dimension: int = 8
) -> ModelBundle:
    item_ids = [item.item_id for item in items]
    users = sorted({row["user_id"] for row in interactions})
    item_index = {item_id: index for index, item_id in enumerate(item_ids)}
    user_index = {user_id: index for index, user_id in enumerate(users)}
    matrix = np.zeros((len(users), len(item_ids)), dtype=np.float64)
    popularity_scores: dict[str, float] = defaultdict(float)
    user_seen: dict[str, list[str]] = defaultdict(list)
    user_topics_raw: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    item_lookup = {item.item_id: item for item in items}

    for row in interactions:
        if row["item_id"] not in item_index:
            continue
        weight = interaction_weight(row)
        user_id = row["user_id"]
        item_id = row["item_id"]
        matrix[user_index[user_id], item_index[item_id]] += weight
        popularity_scores[item_id] += max(0.0, weight)
        if item_id not in user_seen[user_id]:
            user_seen[user_id].append(item_id)
        if weight > 0:
            user_topics_raw[user_id][item_lookup[item_id].topic] += weight

    positive_matrix = np.maximum(matrix, 0.0)
    rank = max(1, min(dimension, min(positive_matrix.shape)))
    u_matrix, singular_values, vt_matrix = np.linalg.svd(positive_matrix, full_matrices=False)
    scale = np.sqrt(singular_values[:rank])
    user_embeddings = normalize_rows(u_matrix[:, :rank] * scale)
    item_embeddings = normalize_rows(vt_matrix[:rank, :].T * scale)

    co_counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for seen_items in user_seen.values():
        positives = [item_id for item_id in seen_items if popularity_scores[item_id] > 0]
        for source in positives:
            for target in positives:
                if source != target:
                    co_counts[source][target] += 1

    co_watch = {
        source: [
            item_id
            for item_id, _ in sorted(targets.items(), key=lambda pair: (-pair[1], pair[0]))[:20]
        ]
        for source, targets in co_counts.items()
    }
    user_topics = {}
    for user_id, topics in user_topics_raw.items():
        total = sum(topics.values()) or 1.0
        user_topics[user_id] = {topic: value / total for topic, value in topics.items()}

    payload_for_version = {
        "items": [asdict(item) for item in items],
        "interactions": interactions,
        "dimension": rank,
    }
    return ModelBundle(
        version=bundle_version(payload_for_version),
        embedding_dimension=rank,
        items=item_lookup,
        popularity=sorted(item_ids, key=lambda item_id: (-popularity_scores[item_id], item_id)),
        popularity_scores=dict(popularity_scores),
        co_watch=co_watch,
        item_vectors={
            item_id: item_embeddings[index].tolist() for item_id, index in item_index.items()
        },
        user_vectors={
            user_id: user_embeddings[index].tolist() for user_id, index in user_index.items()
        },
        user_topics=user_topics,
        user_seen=dict(user_seen),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a versioned recommendation artifact bundle")
    parser.add_argument("--items", default=settings.items_path)
    parser.add_argument("--interactions", default=settings.interactions_path)
    parser.add_argument("--output", default=settings.artifact_path)
    parser.add_argument("--dimension", type=int, default=8)
    arguments = parser.parse_args()
    bundle = build_bundle(
        read_items(arguments.items),
        read_interactions(arguments.interactions),
        dimension=arguments.dimension,
    )
    bundle.save(arguments.output)
    print(f"wrote bundle {bundle.version} with {len(bundle.items)} items to {arguments.output}")


if __name__ == "__main__":
    main()
