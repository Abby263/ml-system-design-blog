from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime

import numpy as np

from .artifacts import Item, ModelBundle


@dataclass
class Candidate:
    item: Item
    retrieval_score: float = 0.0
    sources: set[str] = field(default_factory=set)
    final_score: float = 0.0
    reason: str = ""


@dataclass(frozen=True)
class Recommendation:
    item_id: str
    score: float
    sources: list[str]
    reason: str


@dataclass(frozen=True)
class RecommendationResult:
    model_version: str
    degraded: bool
    failed_sources: list[str]
    recommendations: list[Recommendation]


class RecommendationPipeline:
    def __init__(self, bundle: ModelBundle):
        self.bundle = bundle

    def _add(
        self,
        pool: dict[str, Candidate],
        item_id: str,
        source: str,
        score: float,
    ) -> None:
        item = self.bundle.items.get(item_id)
        if item is None:
            return
        candidate = pool.setdefault(item_id, Candidate(item=item))
        candidate.sources.add(source)
        candidate.retrieval_score = max(candidate.retrieval_score, score)

    def _embedding_query(self, user_id: str, session_items: list[str]) -> np.ndarray | None:
        vectors = []
        if user_id in self.bundle.user_vectors:
            vectors.append(np.asarray(self.bundle.user_vectors[user_id], dtype=np.float64))
        vectors.extend(
            np.asarray(self.bundle.item_vectors[item_id], dtype=np.float64)
            for item_id in session_items
            if item_id in self.bundle.item_vectors
        )
        if not vectors:
            return None
        query = np.mean(vectors, axis=0)
        norm = np.linalg.norm(query)
        return query / norm if norm else query

    def recommend(
        self,
        user_id: str,
        limit: int = 20,
        session_items: list[str] | None = None,
        fail_sources: set[str] | None = None,
    ) -> RecommendationResult:
        session_items = session_items or []
        fail_sources = fail_sources or set()
        pool: dict[str, Candidate] = {}
        known_sources = {"embedding", "co_watch", "popular", "fresh"}
        failed = sorted(known_sources.intersection(fail_sources))

        if "popular" not in fail_sources:
            maximum = max(self.bundle.popularity_scores.values(), default=1.0) or 1.0
            for item_id in self.bundle.popularity[:100]:
                self._add(
                    pool,
                    item_id,
                    "popular",
                    self.bundle.popularity_scores.get(item_id, 0.0) / maximum,
                )

        if "co_watch" not in fail_sources:
            seeds = session_items[-3:] or self.bundle.user_seen.get(user_id, [])[-3:]
            for seed in seeds:
                neighbors = self.bundle.co_watch.get(seed, [])
                for rank, item_id in enumerate(neighbors):
                    self._add(pool, item_id, "co_watch", 1.0 / (rank + 1))

        if "embedding" not in fail_sources:
            query = self._embedding_query(user_id, session_items)
            if query is not None:
                scored = []
                for item_id, vector in self.bundle.item_vectors.items():
                    scored.append((float(np.dot(query, np.asarray(vector))), item_id))
                for score, item_id in sorted(scored, reverse=True)[:100]:
                    self._add(pool, item_id, "embedding", (score + 1.0) / 2.0)

        if "fresh" not in fail_sources:
            newest = sorted(
                self.bundle.items.values(),
                key=lambda item: (item.created_at, item.item_id),
                reverse=True,
            )
            for rank, item in enumerate(newest[:30]):
                self._add(pool, item.item_id, "fresh", 1.0 / (rank + 1))

        degraded = bool(failed)
        if not pool:
            degraded = True
            failed = sorted(known_sources)
            for rank, item_id in enumerate(self.bundle.popularity[: max(limit * 3, 20)]):
                self._add(pool, item_id, "fallback_popular", 1.0 / (rank + 1))

        excluded = set(self.bundle.user_seen.get(user_id, [])).union(session_items)
        topics = self.bundle.user_topics.get(user_id, {})
        now = datetime.now(UTC)
        for candidate in pool.values():
            created = datetime.fromisoformat(candidate.item.created_at.replace("Z", "+00:00"))
            age_days = max(0.0, (now - created).total_seconds() / 86_400)
            freshness = 1.0 / (1.0 + age_days / 30.0)
            topic_affinity = topics.get(candidate.item.topic, 0.0)
            candidate.final_score = (
                0.45 * candidate.retrieval_score
                + 0.25 * topic_affinity
                + 0.20 * candidate.item.quality
                + 0.10 * freshness
            )
            source_priority = ("co_watch", "embedding", "popular", "fresh", "fallback_popular")
            candidate.reason = next(
                (source for source in source_priority if source in candidate.sources),
                "retrieval",
            )

        ranked = sorted(
            (candidate for item_id, candidate in pool.items() if item_id not in excluded),
            key=lambda candidate: (-candidate.final_score, candidate.item.item_id),
        )
        selected: list[Candidate] = []
        remaining = ranked[:]
        while remaining and len(selected) < limit:
            creator_counts = defaultdict(int)
            topic_counts = defaultdict(int)
            for item in selected:
                creator_counts[item.item.creator_id] += 1
                topic_counts[item.item.topic] += 1
            best = max(
                remaining,
                key=lambda candidate: (
                    candidate.final_score
                    - 0.18 * creator_counts[candidate.item.creator_id]
                    - 0.10 * topic_counts[candidate.item.topic],
                    candidate.item.item_id,
                ),
            )
            selected.append(best)
            remaining.remove(best)

        return RecommendationResult(
            model_version=self.bundle.version,
            degraded=degraded,
            failed_sources=failed,
            recommendations=[
                Recommendation(
                    item_id=candidate.item.item_id,
                    score=round(candidate.final_score, 6),
                    sources=sorted(candidate.sources),
                    reason=candidate.reason,
                )
                for candidate in selected
            ],
        )
