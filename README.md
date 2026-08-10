# Designing ML Systems

Code and companion material for the **Designing ML Systems** blog series.

The series builds system design depth by starting from practical software systems, evolving them under real constraints, and then carrying those foundations into ML platforms, generative AI systems, and agentic infrastructure.

**Website:** [designing-ml-systems.vercel.app](https://designing-ml-systems.vercel.app)

The website is generated directly from the folders in [`blogs/`](blogs/). Each numbered folder becomes an article page and its `code/` directory becomes a browsable companion-code section. Pushes to `main` deploy automatically through Vercel.

## Repository structure

Each blog gets its own folder under [`blogs/`](blogs/). Blog folders are numbered so the repo follows the same order as the series.

```text
blogs/
  01-introduction/
    README.md        # article notes / blog companion
    assets/          # HLDs, LLDs, flowcharts, mind maps, and other diagrams
    code/            # runnable code for this blog, if applicable
```

Prefer SVG for technical diagrams so labels remain sharp, searchable, and editable. For implementation-heavy posts, the `code/` directory should include the runnable service, tests, deployment files, load-test scripts, and any local setup instructions needed for that post.

ML system-design articles follow the reusable **[interview and blog template](docs/ml-system-design-interview-template.md)**. It defines the required interview sequence, HLD evolution, first-use terminology rules, interviewer probes, diagram choices, conceptual knowledge checks, and publication checklist. That template is the condensed checklist distilled from the **[full 72-stage interview framework](docs/ai-system-design-interview-framework.md)**, which covers classical ML, RAG, LLM infrastructure, and agentic systems in more depth.

## Run the website locally

```bash
npm install
npm run build
npm run dev
```

The production build is written to `dist/` and contains only static assets.

## Current posts

| # | Blog | Code |
|---|------|------|
| 01 | [Designing ML Systems: Introduction](blogs/01-introduction/) | No executable code for the intro |
| 02 | [Designing a URL Shortener: From One Table to a Global Redirect Plane](blogs/02-url-shortener/) | [FastAPI, PostgreSQL, Redis, worker, tests, and load test](blogs/02-url-shortener/code/) |
| 03 | [Designing a Distributed Rate Limiter: Correct Quotas Across Many Servers](blogs/03-distributed-rate-limiter/) | [FastAPI, Redis Lua token bucket, tests, and load test](blogs/03-distributed-rate-limiter/code/) |
| 04 | [Designing a Notification Platform: Durable Intent, At-Least-Once Delivery, and Provider Reality](blogs/04-notification-platform/) | [FastAPI, transactional outbox, leased worker, provider adapters, callbacks, and tests](blogs/04-notification-platform/code/) |
| 20 | [ML System Design Prerequisites: The Interview Template Before the Case Studies](blogs/20-ml-system-design-prerequisites/) | [Interview worksheet, decision-system contract, capacity calculator, tests, and editable Excalidraw board](blogs/20-ml-system-design-prerequisites/code/) |
| 21 | [Designing a Recommendation System: From a Popularity Baseline to Multi-Stage Ranking at Scale](blogs/21-recommendation-system/) | [Offline trainer, multi-source retrieval, ranking, diversity, temporal evaluation, FastAPI, and tests](blogs/21-recommendation-system/code/) |
| 22 | [Designing Real-Time Fraud Detection: A Decision System Under Adversarial Drift](blogs/22-real-time-fraud-detection/) | [Temporal trainer, rolling features, rules and policy, idempotent FastAPI decisions, delayed labels, and tests](blogs/22-real-time-fraud-detection/code/) |

## Planned direction

The series starts with software-system foundations such as URL shorteners, rate limiters, notification systems, chat systems, storage systems, caching, observability, and checkout/payment flows. It then moves into ML system design: recommendation systems, feature stores, training platforms, model serving, prediction platforms, experimentation, RAG, LLM inference, AI control planes, and multi-tenant enterprise AI platforms.
