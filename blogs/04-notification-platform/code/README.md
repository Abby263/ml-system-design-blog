# Notification platform companion

This example turns the Blog 04 reliability contract into a small runnable workflow. It uses SQLite so the transaction, outbox jobs, leases, retries, and callback deduplication stay visible. Production deployments would normally use PostgreSQL plus a durable broker and independently scaled workers.

No real notification is sent. The adapters are deterministic fakes:

- a recipient containing `retry` is throttled on its first attempt;
- a recipient containing `invalid` gets a terminal endpoint error;
- a recipient containing `reject` gets a terminal request error;
- every other delivery reaches `provider_accepted`.

## Run locally

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e .
uvicorn app.main:app --reload
```

In another terminal, process jobs continuously:

```bash
notification-worker
```

Or process one job at a time to inspect state transitions:

```bash
notification-worker --once
```

## Submit work

```bash
curl -i http://localhost:8000/v1/notifications \
  -H 'Content-Type: application/json' \
  -H 'X-Tenant-Id: demo' \
  -H 'Idempotency-Key: receipt-742' \
  -d '{
    "recipient_id": "user-231",
    "template": "order-receipt",
    "channels": ["email", "push"],
    "data": {"order_id": "742"},
    "priority": "transactional"
  }'
```

Repeat the same request and key to receive the original notification ID. Change the body while reusing the key to receive `409 Conflict`.

## Send a signed callback

Replace the delivery ID, then calculate an HMAC over the exact body bytes:

```bash
body='{"event_id":"evt-1","delivery_id":"dlv_REPLACE","status":"delivered"}'
signature=$(printf '%s' "$body" | openssl dgst -sha256 -hmac 'local-development-secret' -hex | awk '{print $2}')
curl -i http://localhost:8000/v1/provider-callbacks/fake-email \
  -H 'Content-Type: application/json' \
  -H "X-Provider-Signature: $signature" \
  -d "$body"
```

The same provider and event ID is accepted once. A late `failed` event cannot move a `delivered` delivery backward.

## Docker Compose

```bash
docker compose up --build
```

The API and worker share a named SQLite volume for this local demonstration. That is not a horizontally scalable database topology; it is a compact way to inspect the workflow without external accounts.

## Checks

```bash
python -m unittest discover -s tests
ruff check app tests
ruff format --check app tests
docker compose config --quiet
```
