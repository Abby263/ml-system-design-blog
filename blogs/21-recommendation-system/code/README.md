# Recommendation-system companion

This runnable example implements the core seams from Blog 21: an offline artifact builder, four candidate sources, a lightweight ranker, diversity-aware re-ranking, a versioned model bundle, temporal evaluation, and explicit degraded-mode behavior.

It intentionally uses exact NumPy similarity search and JSON artifacts so the mechanics remain inspectable. At production scale, replace those seams with an ANN index, feature store, model registry, event stream, and independently scaled services as described in the article.

## Run locally

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
recommendation-train
recommendation-evaluate --k 5
uvicorn app.main:app --reload
```

Request recommendations for an existing user:

```bash
curl 'http://localhost:8000/v1/recommendations?user_id=user-001&limit=5'
```

Add short-session intent or simulate a failed retriever:

```bash
curl 'http://localhost:8000/v1/recommendations?user_id=new-user&session_items=video-001,video-005&fail_sources=embedding'
```

The response reports the model version, failed sources, degradation state, merged candidate provenance, and final score. Fail all four sources to exercise the popularity fallback.

## Docker Compose

```bash
docker compose up --build
```

The one-shot trainer writes a bundle into a shared volume before the API starts. This mirrors immutable artifact promotion without requiring a cloud account.

## Checks

```bash
python -m pytest
ruff check app tests
ruff format --check app tests
docker compose config --quiet
```

The bundled evaluator removes each eligible user's latest positive interaction, rebuilds every learned artifact from the remaining events, and then reports Recall@K and NDCG@K. The tiny sample is for mechanics, not for judging model quality.
