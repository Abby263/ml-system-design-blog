# Real-time fraud-decision companion

This implementation makes the Blog 22 contracts executable: chronological class-weighted training, immutable model artifacts, rolling online features, idempotent decisions, deterministic rules, four-action policy, degraded serving, and append-only delayed labels.

SQLite is intentionally used as one local atomic boundary. `BEGIN IMMEDIATE` serializes the feature read and decision append so two concurrent attempts cannot both observe stale velocity, while an idempotent retry returns the original decision without incrementing a counter. Production systems replace this seam with partitioned stream state, an online feature store, and a durable decision ledger.

## Run locally

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
fraud-train
fraud-evaluate
uvicorn app.main:app --reload
```

Submit a payment:

```bash
curl http://localhost:8000/v1/risk-decisions \
  -H 'Content-Type: application/json' \
  -H 'Idempotency-Key: payment-attempt-742' \
  -d '{
    "transaction_id": "txn-742",
    "event_time": "2026-08-10T12:00:00Z",
    "account_id": "account-19",
    "account_created_at": "2026-08-10T10:30:00Z",
    "card_token": "card-token-8a",
    "device_id": "device-a91",
    "ip_prefix": "203.0.113.0/24",
    "country": "CA",
    "merchant_id": "merchant-demo",
    "amount_minor": 90000,
    "currency": "CAD",
    "cvv_result": "match"
  }'
```

Repeat it unchanged to receive the original decision with `idempotent_replay=true`. Change the amount while reusing the key to receive `409 Conflict`.

Exercise model failure or stale streaming features:

```bash
curl 'http://localhost:8000/v1/risk-decisions?fail_model=true' ...
curl 'http://localhost:8000/v1/risk-decisions?stale_features=true' ...
```

Both responses declare degradation and unavailable sources. The fallback combines deterministic rules with an amount/tenure-aware policy rather than silently returning a normal score.

## Delayed labels

```bash
curl http://localhost:8000/v1/risk-decisions/DECISION_ID/labels \
  -H 'Content-Type: application/json' \
  -d '{
    "label_type": "chargeback",
    "label_value": "fraud",
    "source": "issuer-feed",
    "confidence": 1.0,
    "observed_at": "2026-09-10T12:00:00Z"
  }'
```

Corrections point to `correction_of`; they do not rewrite the historical decision or earlier label.

## Docker Compose

```bash
docker compose up --build
```

The one-shot trainer writes an immutable model into a shared volume before the API starts. A named volume preserves the local decision ledger.

## Checks

```bash
python -m pytest
ruff check app tests
ruff format --check app tests
docker compose config --quiet
```

The sample data is synthetic and exists to make temporal splitting and the contracts inspectable; its metrics are not evidence of production model quality.
