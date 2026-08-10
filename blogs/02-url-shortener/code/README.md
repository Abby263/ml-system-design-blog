# URL shortener companion service

This is the production-shaped implementation used in the second **Designing ML Systems** article. It keeps the redirect path small, treats PostgreSQL as the source of truth, uses Redis as a disposable cache, and moves click aggregation to a separate worker.

## Run locally

```bash
docker compose up --build
```

Create and follow a link:

```bash
curl -sS http://localhost:8000/api/v1/links \
  -H 'content-type: application/json' \
  -d '{"target_url":"https://example.com/a/long/path"}'

curl -i http://localhost:8000/1000000
```

Useful endpoints:

- API documentation: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/healthz`
- Prometheus metrics: `http://localhost:8000/metrics/`

## Run the fast tests

These tests cover the dependency-free Base62 and URL-policy core:

```bash
python -m unittest discover -s tests
```

## Load test the hot redirect path

Install [k6](https://grafana.com/docs/k6/latest/set-up/install-k6/), create a link, and pass its code:

```bash
k6 run -e SHORT_CODE=1000000 -e RPS=500 load/redirects.js
```

The demo deliberately does not pretend to be the final global architecture. The article explains what changes when ID generation, reads, analytics, and edge caching must span regions.
