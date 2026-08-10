import math


def recall_at_k(actual: set[str], predicted: list[str], k: int) -> float:
    if not actual:
        return 0.0
    return len(actual.intersection(predicted[:k])) / len(actual)


def ndcg_at_k(relevance: dict[str, float], predicted: list[str], k: int) -> float:
    def gain(items: list[str]) -> float:
        return sum(
            (2 ** relevance.get(item_id, 0.0) - 1) / math.log2(position + 2)
            for position, item_id in enumerate(items[:k])
        )

    ideal = sorted(relevance, key=relevance.get, reverse=True)[:k]
    ideal_gain = gain(ideal)
    return gain(predicted) / ideal_gain if ideal_gain else 0.0
