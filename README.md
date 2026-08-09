# Designing ML Systems

Code and companion material for the **Designing ML Systems** blog series.

The series builds system design depth by starting from practical software systems, evolving them under real constraints, and then carrying those foundations into ML platforms, generative AI systems, and agentic infrastructure.

## Repository structure

Each blog gets its own folder under [`blogs/`](blogs/). Blog folders are numbered so the repo follows the same order as the series.

```text
blogs/
  01-introduction/
    README.md        # article notes / blog companion
    code/            # runnable code for this blog, if applicable
```

For implementation-heavy posts, the `code/` directory should include the runnable service, tests, deployment files, load-test scripts, and any local setup instructions needed for that post.

## Current posts

| # | Blog | Code |
|---|------|------|
| 01 | [Designing ML Systems: Introduction](blogs/01-introduction/) | No executable code for the intro |

## Planned direction

The series starts with software-system foundations such as URL shorteners, rate limiters, notification systems, chat systems, storage systems, caching, observability, and checkout/payment flows. It then moves into ML system design: recommendation systems, feature stores, training platforms, model serving, prediction platforms, experimentation, RAG, LLM inference, AI control planes, and multi-tenant enterprise AI platforms.

