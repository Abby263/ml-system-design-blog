# Distributed rate limiter companion service

This service implements an atomic Redis token bucket with server-owned time, integer-scaled tokens, privacy-preserving partition keys, explicit fail-open/fail-closed policies, Prometheus metrics, and HTTP rate-limit feedback.

## Run it

```bash
docker compose up --build
```

The public endpoint permits a burst of 20 requests and refills at 5 requests/second:

```bash
curl -i http://localhost:8000/public-data -H 'X-API-Key: demo-client'
```

The expensive endpoint permits a burst of 3 and refills at 0.2 requests/second:

```bash
curl -i -X POST http://localhost:8000/expensive-report \
  -H 'X-API-Key: demo-client'
```

When Redis is unavailable, `/public-data` fails open and annotates the response. `/expensive-report` fails closed with `503` because unbounded admission would risk expensive downstream work.

## Checks

```bash
python -m unittest discover -s tests
ruff check app tests
ruff format --check app tests
docker compose config --quiet
```

## Load test

```bash
k6 run -e RPS=50 load/rate_limit.js
```

The response uses `Retry-After` on `429`. It also demonstrates the `RateLimit-Policy` and `RateLimit` fields from the active IETF Internet-Draft; production APIs should version their public header contract while that draft remains a work in progress.
