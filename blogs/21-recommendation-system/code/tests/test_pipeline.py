from pathlib import Path

from fastapi.testclient import TestClient

from app.artifacts import ModelBundle
from app.pipeline import RecommendationPipeline
from app.train import build_bundle, read_interactions, read_items


ROOT = Path(__file__).parents[1]


def bundle() -> ModelBundle:
    return build_bundle(
        read_items(str(ROOT / "data/items.csv")),
        read_interactions(str(ROOT / "data/interactions.csv")),
        dimension=6,
    )


def test_known_user_excludes_seen_items_and_diversifies() -> None:
    model = bundle()
    result = RecommendationPipeline(model).recommend("user-001", limit=5)
    seen = set(model.user_seen["user-001"])
    returned = [recommendation.item_id for recommendation in result.recommendations]

    assert returned
    assert not seen.intersection(returned)
    assert len(returned) == len(set(returned))
    assert any("embedding" in recommendation.sources for recommendation in result.recommendations)


def test_unknown_user_uses_non_personalized_sources() -> None:
    result = RecommendationPipeline(bundle()).recommend("new-user", limit=4)

    assert len(result.recommendations) == 4
    assert all(
        set(recommendation.sources).intersection({"popular", "fresh"})
        for recommendation in result.recommendations
    )


def test_total_source_failure_uses_explicit_fallback() -> None:
    result = RecommendationPipeline(bundle()).recommend(
        "new-user",
        limit=3,
        fail_sources={"embedding", "co_watch", "popular", "fresh"},
    )

    assert result.degraded is True
    assert result.failed_sources == ["co_watch", "embedding", "fresh", "popular"]
    assert len(result.recommendations) == 3
    assert all(item.sources == ["fallback_popular"] for item in result.recommendations)


def test_health_and_recommendation_api(tmp_path, monkeypatch) -> None:
    artifact = tmp_path / "bundle.json"
    bundle().save(str(artifact))
    monkeypatch.setattr("app.main.settings.artifact_path", str(artifact))

    from app.main import app

    with TestClient(app) as client:
        health = client.get("/healthz")
        response = client.get(
            "/v1/recommendations",
            params={"user_id": "user-002", "limit": 4},
        )

    assert health.status_code == 200
    assert response.status_code == 200
    assert len(response.json()["recommendations"]) == 4


def test_api_rejects_unknown_failure_source(tmp_path, monkeypatch) -> None:
    artifact = tmp_path / "bundle.json"
    bundle().save(str(artifact))
    monkeypatch.setattr("app.main.settings.artifact_path", str(artifact))

    from app.main import app

    with TestClient(app) as client:
        response = client.get(
            "/v1/recommendations",
            params={"user_id": "user-002", "fail_sources": "mystery"},
        )

    assert response.status_code == 422
