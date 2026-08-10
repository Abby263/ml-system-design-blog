def average_precision(labels: list[int], scores: list[float]) -> float:
    positives = sum(labels)
    if positives == 0:
        return 0.0
    ranked = sorted(zip(scores, labels, strict=True), reverse=True)
    true_positives = 0
    total = 0.0
    for rank, (_, label) in enumerate(ranked, start=1):
        if label:
            true_positives += 1
            total += true_positives / rank
    return total / positives


def precision_recall(
    labels: list[int], scores: list[float], threshold: float
) -> tuple[float, float]:
    predicted = [score >= threshold for score in scores]
    true_positives = sum(label == 1 and decision for label, decision in zip(labels, predicted))
    false_positives = sum(label == 0 and decision for label, decision in zip(labels, predicted))
    false_negatives = sum(label == 1 and not decision for label, decision in zip(labels, predicted))
    precision = true_positives / max(1, true_positives + false_positives)
    recall = true_positives / max(1, true_positives + false_negatives)
    return precision, recall


def expected_cost(labels: list[int], scores: list[float], threshold: float) -> float:
    cost = 0.0
    for label, score in zip(labels, scores, strict=True):
        blocked = score >= threshold
        if label == 1 and not blocked:
            cost += 100.0
        elif label == 0 and blocked:
            cost += 8.0
    return cost / max(1, len(labels))
