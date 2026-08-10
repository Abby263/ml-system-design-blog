import argparse
from collections import defaultdict

from .metrics import ndcg_at_k, recall_at_k
from .pipeline import RecommendationPipeline
from .settings import settings
from .train import build_bundle, read_interactions, read_items


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate on each user's last positive event")
    parser.add_argument("--items", default=settings.items_path)
    parser.add_argument("--interactions", default=settings.interactions_path)
    parser.add_argument("--k", type=int, default=10)
    arguments = parser.parse_args()

    all_rows = read_interactions(arguments.interactions)
    events: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in all_rows:
        if row["event_type"] != "hide":
            events[row["user_id"]].append(row)

    held_out: dict[str, dict[str, str]] = {}
    for user_id, rows in events.items():
        ordered = sorted(rows, key=lambda row: row["event_time"])
        if len(ordered) >= 2:
            held_out[user_id] = ordered[-1]

    # Rebuild from only pre-cutoff events. Loading the full artifact here would let the
    # target interaction influence embeddings, co-watch edges, and popularity.
    training_rows = [row for row in all_rows if row is not held_out.get(row["user_id"])]
    bundle = build_bundle(read_items(arguments.items), training_rows)
    pipeline = RecommendationPipeline(bundle)
    recalls = []
    ndcgs = []
    for user_id, target_row in held_out.items():
        target = target_row["item_id"]
        predicted = [
            item.item_id
            for item in pipeline.recommend(
                user_id=user_id,
                limit=arguments.k,
            ).recommendations
        ]
        recalls.append(recall_at_k({target}, predicted, arguments.k))
        ndcgs.append(ndcg_at_k({target: 1.0}, predicted, arguments.k))
    count = len(recalls)
    print(
        f"users={count} recall@{arguments.k}={sum(recalls) / count:.4f} "
        f"ndcg@{arguments.k}={sum(ndcgs) / count:.4f}"
        if count
        else "no evaluable users"
    )


if __name__ == "__main__":
    main()
