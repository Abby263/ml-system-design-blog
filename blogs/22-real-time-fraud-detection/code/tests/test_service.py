from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.metrics import average_precision, precision_recall
from app.train import fit_bundle, read_rows


ROOT = Path(__file__).parents[1]


@pytest.fixture
def client(tmp_path, monkeypatch):
    rows = read_rows(str(ROOT / "data/transactions.csv"))
    artifact = tmp_path / "model.json"
    fit_bundle(rows[:28], epochs=500).save(str(artifact))
    monkeypatch.setattr("app.main.settings.artifact_path", str(artifact))
    monkeypatch.setattr("app.main.settings.database_path", str(tmp_path / "fraud.db"))

    from app.main import app

    with TestClient(app) as test_client:
        yield test_client, app


def payment(
    transaction_id: str,
    event_time: datetime,
    *,
    amount_minor: int = 2_500,
    cvv_result: str = "match",
) -> dict[str, object]:
    return {
        "transaction_id": transaction_id,
        "event_time": event_time.isoformat(),
        "account_id": f"account-{transaction_id}",
        "account_created_at": (event_time - timedelta(days=90)).isoformat(),
        "card_token": "card-shared",
        "device_id": "device-shared",
        "ip_prefix": "203.0.113.0/24",
        "country": "CA",
        "merchant_id": "merchant-demo",
        "amount_minor": amount_minor,
        "currency": "CAD",
        "cvv_result": cvv_result,
    }


def test_idempotent_retry_does_not_increment_velocity(client) -> None:
    test_client, app = client
    event_time = datetime(2026, 8, 10, 12, 0, tzinfo=UTC)
    payload = payment("txn-1", event_time)

    first = test_client.post(
        "/v1/risk-decisions", json=payload, headers={"Idempotency-Key": "attempt-1"}
    )
    replay = test_client.post(
        "/v1/risk-decisions", json=payload, headers={"Idempotency-Key": "attempt-1"}
    )

    assert first.status_code == 200
    assert replay.status_code == 200
    assert first.json()["decision_id"] == replay.json()["decision_id"]
    assert replay.json()["idempotent_replay"] is True
    assert app.state.store.decision_count() == 1
    assert replay.json()["features"]["card_attempt_count_10m"] == 1.0


def test_reusing_key_with_another_body_conflicts(client) -> None:
    test_client, _ = client
    event_time = datetime(2026, 8, 10, 12, 0, tzinfo=UTC)
    original = payment("txn-1", event_time)
    changed = payment("txn-1", event_time, amount_minor=9_999)

    assert (
        test_client.post(
            "/v1/risk-decisions", json=original, headers={"Idempotency-Key": "attempt-1"}
        ).status_code
        == 200
    )
    response = test_client.post(
        "/v1/risk-decisions", json=changed, headers={"Idempotency-Key": "attempt-1"}
    )

    assert response.status_code == 409


def test_velocity_and_failed_cvv_trigger_hard_block(client) -> None:
    test_client, _ = client
    start = datetime(2026, 8, 10, 12, 0, tzinfo=UTC)
    responses = []
    for index in range(4):
        responses.append(
            test_client.post(
                "/v1/risk-decisions",
                json=payment(
                    f"txn-{index}",
                    start + timedelta(seconds=index),
                    cvv_result="fail",
                ),
                headers={"Idempotency-Key": f"attempt-{index}"},
            )
        )

    final = responses[-1].json()
    assert all(response.status_code == 200 for response in responses)
    assert final["features"]["card_attempt_count_10m"] == 4.0
    assert final["action"] == "block"
    assert "card_velocity_10m" in final["reason_codes"]


def test_model_failure_is_explicit_and_uses_fallback(client) -> None:
    test_client, _ = client
    payload = payment("txn-fallback", datetime(2026, 8, 10, 12, 0, tzinfo=UTC))
    response = test_client.post(
        "/v1/risk-decisions?fail_model=true",
        json=payload,
        headers={"Idempotency-Key": "fallback"},
    )

    assert response.status_code == 200
    assert response.json()["degraded"] is True
    assert response.json()["model_version"] == "rules-only"
    assert response.json()["unavailable_sources"] == ["model"]


def test_policy_challenges_high_value_new_account(client) -> None:
    test_client, _ = client
    event_time = datetime(2026, 8, 10, 12, 0, tzinfo=UTC)
    payload = payment("txn-high-value", event_time, amount_minor=90_000)
    payload["account_created_at"] = (event_time - timedelta(minutes=90)).isoformat()
    response = test_client.post(
        "/v1/risk-decisions",
        json=payload,
        headers={"Idempotency-Key": "high-value"},
    )

    assert response.status_code == 200
    assert response.json()["action"] == "challenge"
    assert "high_value_new_account_policy" in response.json()["reason_codes"]


def test_delayed_label_appends_to_existing_decision(client) -> None:
    test_client, _ = client
    payload = payment("txn-label", datetime(2026, 8, 10, 12, 0, tzinfo=UTC))
    decision = test_client.post(
        "/v1/risk-decisions", json=payload, headers={"Idempotency-Key": "label-attempt"}
    ).json()
    response = test_client.post(
        f"/v1/risk-decisions/{decision['decision_id']}/labels",
        json={
            "label_type": "chargeback",
            "label_value": "fraud",
            "source": "issuer-feed",
            "confidence": 1.0,
            "observed_at": "2026-09-10T12:00:00Z",
        },
    )

    assert response.status_code == 201
    assert response.json()["decision_id"] == decision["decision_id"]
    assert response.json()["label_value"] == "fraud"


def test_imbalanced_metrics() -> None:
    labels = [0, 0, 1, 0, 1]
    scores = [0.1, 0.2, 0.9, 0.3, 0.8]

    assert average_precision(labels, scores) == 1.0
    assert precision_recall(labels, scores, 0.5) == (1.0, 1.0)
