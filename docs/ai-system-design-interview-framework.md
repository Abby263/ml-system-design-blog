# Designing ML Systems — End-to-End AI System Design Interview Framework

This is the exhaustive reference framework behind every article in this series: classical ML, Generative AI, RAG, LLM infrastructure, Agentic AI, and AI platforms all draw on it.

It is intentionally comprehensive. It is not intended to be recited from top to bottom, in a blog or in an interview. An experienced architect moves through it naturally, spending time where the problem is difficult and skipping areas that do not materially affect the design.

The interview should feel like a conversation. The whiteboard should evolve alongside that conversation. The architecture should become more complicated only when a requirement forces it to.

Day-to-day writing in this repository follows the condensed, required version of this framework in **[the interview and blog template](ml-system-design-interview-template.md)**. This document is the exhaustive source those requirements are distilled from — use it when a new article needs to work out which stages matter for its problem, or when the condensed template doesn't have enough detail for a specific decision (training architecture, multi-region, agent/tool boundaries, and so on).

## 1. Start With the Interview Prompt

Write the problem at the top of the canvas. For example: *Design a real-time fraud detection platform.* Or: *Design an enterprise RAG system for ten million users.* Or: *Design an AI customer-support agent.*

Do not start drawing infrastructure yet. The first job is understanding what we have actually been asked to build.

A good opening sounds something like:

> **Us:** Before getting into architecture, I'd like to clarify the product outcome, the scale we're designing for, and which parts genuinely need intelligence. Then I'll sketch a simple version and evolve it as we identify bottlenecks.

That also gives the interviewer a roadmap without sounding rehearsed.

## 2. Clarify the Product and Functional Requirements

Understand the user journey. Ask only questions capable of changing the architecture.

For fraud: Does the decision happen before authorization?
For RAG: Do documents have user-level or group-level permissions?
For an agent: Can the system execute actions autonomously, or does it only recommend them?
For recommendations: Are we ranking from an existing candidate set or responsible for candidate generation too?

Capture the resulting assumptions on the whiteboard, and keep them visible throughout the interview:

```text
FUNCTIONAL REQUIREMENTS

User submits ...
System returns ...
System can ...
System cannot ...
Human approval required for ...
```

## 3. Clarify Non-Functional Requirements

Now establish architectural constraints: latency, throughput, availability, consistency, durability, geography, data residency, privacy, security, cost, freshness.

For AI systems we may additionally ask about model-quality expectations, time to first token, feature freshness, maximum context size, tool-execution duration, and whether external model providers are permitted.

A useful whiteboard corner might look like:

```text
SCALE / NFR

Peak              10K RPS
P99                <100 ms
Availability       99.99%
Regions            NA / EU / APAC
Data residency     Required
```

## 4. Define the Intelligence Boundary

Before selecting a model, answer: **which parts of this problem actually require intelligence?** This is one of the most important AI architecture questions.

For fraud:

```text
behaviour + transaction
        ↓
     ML model
        ↓
    risk score
```

But regulatory rules remain deterministic.

For RAG:

```text
Question
   ↓
Retrieval
   ↓
LLM generation
```

But authentication and authorization remain deterministic.

For an agent:

```text
Understand goal
      ↓
Decide action
      ↓
Execute tool
```

But tool permission checks must remain deterministic.

A mature design frequently looks like:

```text
Deterministic System
        │
        ▼
Bounded AI Decision
        │
        ▼
Deterministic Validation
```

rather than allowing an LLM to control everything.

## 5. Define the Output or Decision

What exactly does the intelligent system produce?

Fraud: `risk score`. Business system: `APPROVE / CHALLENGE / REVIEW / DECLINE`. RAG: `answer, citations, confidence / provenance`. Agent: `response, tool action, workflow transition, approval request, escalation`.

Separate *prediction* from *business decision* whenever possible. This allows decision policy to evolve independently from the model.

## 6. Define Success

We usually need three layers of metrics.

**Product / Business.** For fraud this could be fraud loss and false declines. For recommendations it could be engagement or conversion. For customer support it could be successful resolution and escalation rate.

**AI / ML quality.** Precision, recall, NDCG, calibration, groundedness, retrieval recall, task success, tool-selection accuracy — whatever actually fits the problem.

**System.** Latency, availability, throughput, errors, cost.

We should explicitly recognize that a better model metric does not automatically mean a better product.

## 7. Estimate Scale

Now perform the calculations that affect architecture.

Traditional: `RPS, concurrent requests, storage, bandwidth, read/write ratio`.
ML: `predictions/sec, features/prediction, feature reads/sec, training examples, model size, retraining frequency`.
RAG: `documents, chunks/document, total vectors, retrieval QPS, top-k, embedding throughput`.
LLM: `input tokens/sec, output tokens/sec, concurrent sequences, average context, GPU throughput, KV-cache requirement`.
Agents: `tasks/sec, steps/task, tool calls/task, parallel tools, average task duration`.

Put only important derived values on the canvas. Those numbers should later justify architectural decisions.

## 8. Identify the Critical Path

Before drawing the full system, determine: what must happen before the user receives a result?

Fraud: `Payment → Feature retrieval → Model → Decision`.
RAG: `Query → Auth → Retrieval → Reranking → LLM → First token`.
Agent: `Request → Reason → Required tools → Decision`.

Then explicitly separate background work:

```text
USER / CRITICAL PATH
────────────────────────►

BACKGROUND / ASYNC
- - - - - - - - - - - -►
```

This is one of the standard drawing conventions for this series.

## 9. Draw HLD V0 — The Simplest Thing That Works

Never begin with the final architecture. For example:

```text
Client
   │
   ▼
Application
   │
   ▼
Database / Model
```

Ask: could this satisfy the current requirements? If yes, keep it. Complexity must be earned — this is KISS and YAGNI applied directly to architecture.

## 10. Walk Through One Request

Before adding components, trace one real request.

RAG: `Question → retrieve documents → construct context → model → answer`.
Fraud: `Transaction → features → model → policy → decision`.
Agent: `Goal → choose tool → tool result → decide next action → finish`.

This reveals missing dependencies much faster than drawing infrastructure randomly.

## 11. Understand the Data

Identify every meaningful data category.

Conventional ML: training data, labels, features, prediction outputs, feedback.
RAG: source documents, chunks, embeddings, metadata, ACLs, versions.
Agents: session state, workflow state, tool outputs, memory, audit history.

Ask: where does it originate? Who owns it? How quickly does it change? How long should it live? Does it contain sensitive information? Can users delete it? Which components may access it?

## 12. Design Data Ingestion

If data changes, determine how changes enter the platform: polling, webhooks, CDC, event streams, batch pipelines, scheduled ingestion.

For RAG:

```text
Drive / SharePoint / Slack
          │
          ▼
      Connectors
          │
          ▼
     Change Feed
          │
          ▼
 Parse → Chunk → Embed → Index
```

Discuss updates, deletions, schema changes, permissions changes, retries, idempotency.

## 13. Feature / Retrieval / Context / Memory Design

This branch depends on the system.

**Classical ML.** Features, batch versus streaming, online versus offline, freshness, feature store, point-in-time correctness, training-serving skew.

**RAG.** Chunking, lexical search, vector search, hybrid search, metadata filtering, ACL filtering, reranking, context construction.

**GenAI.** Prompt/context composition, conversation context, tool context, structured outputs.

**Agents.** Working memory, conversation memory, workflow state, long-term memory, retrieved knowledge, tool results.

The unifying question: what information must the intelligence layer have at decision time?

## 14. Establish the Simplest Baseline

Never jump immediately to maximum AI complexity.

Fraud: `rules → logistic regression → GBDT → advanced model`.
RAG: `BM25 → vector retrieval → hybrid + reranking`.
Agent: `deterministic workflow → workflow + LLM → single agent with tools → planner/executor → multi-agent`.

Ask: what additional requirement justifies the next level of complexity?

## 15. Compare Major Design Alternatives

This is where experienced architectural reasoning becomes visible. For each important choice, discuss at least one plausible alternative: SQL vs NoSQL, polling vs webhook, Kafka vs queue, monolith vs microservice, hosted vs self-hosted model, vector-only vs hybrid retrieval, workflow vs agent, single-agent vs multi-agent, CPU vs GPU inference.

Compare on quality, latency, cost, reliability, consistency, operational complexity, security, scalability, explainability. Then choose.

Not:

> Redis is fast.

But:

> Local caching gives us lower latency, but Redis gives the entire service fleet a shared cache. Given that mappings are frequently reused across replicas, I'll take the network hop for better consistency and shared utilization.

## 16. Define the Core AI Flow

Now draw the core intelligence pipeline clearly, before adding operational infrastructure.

ML: `Request → Features → Model → Decision`.
RAG: `Query → Retrieve → Rerank → Context → LLM → Answer`.
Agent: `Goal → Reason → Choose action → Tool → Observe → Continue / Finish`.

## 17. Decide Deterministic vs Agentic

Especially for GenAI, explicitly ask: do we actually need an agent?

If the sequence is known — `Validate → Retrieve → Generate → Verify` — use a workflow.

If the model must dynamically decide what to do — `Goal → determine next action → execute → inspect → continue` — an agent becomes justified.

Frequently the best architecture is a deterministic outer workflow wrapping a bounded agentic stage, rather than fully autonomous execution.

## 18. Agent / Tool / Node / Sub-Agent Boundaries

For Agentic AI, make responsibilities explicit. An agent reasons toward a goal. A tool performs a bounded capability. A node is an execution step. A sub-agent independently reasons about a delegated goal.

```text
Support Agent
    │
    ├── Search Tool
    ├── Order Tool
    │
    └── Refund Agent
           │
           └── Refund Tool
```

Don't call every helper function an agent.

## 19. Training Architecture

Where training exists, design it separately:

```text
Raw Data
    │
    ▼
Validation
    │
    ▼
Feature / Label Pipeline
    │
    ▼
Training Dataset
    │
    ▼
Train
    │
    ▼
Evaluate
    │
    ▼
Model Registry
```

Discuss data versioning, labels, sampling, leakage, class imbalance, splits, reproducibility, experiment tracking, hyperparameter tuning.

## 20. Evaluation Architecture

Important enough to separate from training. Offline evaluation should run before deployment.

ML: precision/recall/calibration/business simulations.
RAG: retrieval quality separately from generation quality.
Agents: task success, trajectory correctness, tool selection, tool arguments, unnecessary steps, unsafe actions.
LLMs: golden datasets, human evaluation, model judges where appropriate, regression suites.

Evaluation should become a release gate.

## 21. Online Serving / Inference Architecture

Now design the production path in detail.

```text
Gateway
   │
   ▼
Serving API
   │
   ├── Feature / Retrieval Service
   ├── Model / LLM
   └── Policy / Decision
```

Discuss latency budgets:

```text
Total P99              100 ms
Network                 10 ms
Feature lookup          20 ms
Inference               25 ms
Decision                 5 ms
Headroom                40 ms
```

Numbers are illustrative. The discipline matters.

## 22. Long-Running / Durable Workflows

For workflows taking seconds or minutes, avoid keeping everything tied to one HTTP request. Consider queues, workflow engines, checkpointing, durable state, callbacks, resume semantics.

```text
POST /tasks
    │
    ▼
Task Store
    │
    ▼
Durable Workflow
    │
    ▼
Agent / Tools
```

Especially important for Agentic AI.

## 23. State and Memory

Define separate state categories: request state, session state, conversation state, workflow state, long-term memory.

Ask: what survives a crash? What survives a session? What gets shown to the model? What can be deleted? What is authoritative? What is merely derived?

Avoid dumping unlimited history into model context.

## 24. Tool Design

Treat tools like production APIs: clear responsibility, strict schema, validation, authentication, authorization, timeouts, retries, idempotency, structured errors.

A model requesting an action does not authorize the action. Authorization must live outside the model.

## 25. Human-in-the-Loop

For consequential operations, define explicit boundaries:

```text
Agent proposes action
        │
        ▼
Policy
   ┌────┴─────┐
Low risk   High risk
   │           │
Execute     Human Approval
```

Human approval is an architectural component, not just a prompt instruction.

## 26. API Design

Define real interfaces. Prefer business contracts:

```text
POST /v1/fraud/evaluate
POST /v1/search
POST /v1/support/tasks
```

rather than implementation details (`POST /predict-xgboost`, `POST /run-gpt`).

Cover as relevant: request/response schema, authentication, authorization, idempotency, pagination, timeouts, versioning, streaming, error semantics.

## 27. Database Access Patterns First

Before choosing databases, list the dominant access patterns:

```text
transaction_id → transaction
customer_id → recent transactions
document_id → document
tenant + entity → state
```

Then choose storage. Do not choose DynamoDB because "NoSQL scales." Choose it because its access model matches the workload.

## 28. Database / ER Design

When relational data matters, draw an ER diagram. Show PK, FK, UNIQUE constraints, important indexes, relationships, partition keys when relevant.

```text
CUSTOMER
 PK customer_id
       │ 1
       │
       │ N
TRANSACTION
 PK transaction_id
 FK customer_id
 INDEX(customer_id, event_time)
       │
       │ 1
FRAUD_DECISION
 PK decision_id
 FK transaction_id
```

Then discuss evolution at scale: replication, partitioning, sharding, archival, hot/cold storage.

## 29. Storage Architecture

AI systems frequently need several stores: OLTP database, cache, object store, search index, vector store, feature store, event log, workflow store, data lake, warehouse, model registry.

Every store should answer: why does this need to exist? If there is no convincing answer, remove it.

## 30. Caching

Identify expensive repeatable operations. Possible caches: browser/edge cache, local application cache, Redis, feature cache, retrieval cache, embedding cache, semantic response cache, prompt-prefix/KV cache.

Discuss TTL, invalidation, freshness, stampede, hot keys, tenant isolation, ACL sensitivity.

## 31. Messaging and Streaming

Introduce asynchronous infrastructure only when required.

Use queues for background jobs, decoupling, retries, load smoothing. Use event streams when multiple consumers need events, ordering/partitioning matters, event replay matters, or continuous stateful processing matters.

Discuss partitions, consumer groups, ordering, delivery semantics, dead-letter queues, schema evolution, backpressure.

## 32. Concurrency

Ask: what happens when multiple requests touch the same thing? Discuss race conditions, atomicity, optimistic locking, pessimistic locking, mutex, semaphore, distributed lock, serialization through a queue. Draw the race rather than hiding it in prose.

## 33. Async, Threads and Processes

Ask whether work is I/O or CPU bound.

```text
I/O-bound
→ async / event loop

CPU-bound
→ processes / workers

limited downstream concurrency
→ semaphore

parallel independent work
→ bounded concurrency
```

Also consider connection pools, thread pools, worker pools, deadlocks, starvation.

## 34. Sequence Diagram

Whenever ordering matters, draw one — useful for distributed requests, retries, tool calls, streaming, human approval, async processing, transactions.

```text
Client      API      Features      Model
  │          │           │            │
  │ request  │           │            │
  ├─────────►│           │            │
  │          │ lookup    │            │
  │          ├──────────►│            │
  │          │◄──────────┤            │
  │          │ score                  │
  │          ├───────────────────────►│
  │          │◄───────────────────────┤
  │◄─────────┤                        │
```

## 35. Low-Level Design

Choose one component worth zooming into:

```text
FraudDecisionService
    │
    ├── FeatureProvider
    ├── RiskScorer
    ├── RuleEvaluator
    └── DecisionPolicy
```

Then move from services to classes, interfaces, and responsibilities.

## 36. Class Diagram / UML

Show important classes, interfaces, composition, inheritance only when justified, and dependencies. Avoid giant diagrams containing every implementation detail — the diagram should answer a design question.

## 37. Apply SOLID

Don't say "we use SOLID." Show it.

**Single Responsibility.** Does the component have too many reasons to change?
**Open/Closed.** Can new behaviours be introduced without rewriting orchestration?
**Liskov Substitution.** Do implementations correctly honour their contracts?
**Interface Segregation.** Are interfaces focused rather than enormous?
**Dependency Inversion.** Does business logic depend on abstractions rather than infrastructure details?

## 38. Apply DRY

Think of DRY as avoiding duplicated *knowledge*, not simply duplicated syntax. Important AI example: training and serving feature logic independently implementing the same transformation can create training-serving skew. That is a meaningful DRY problem.

## 39. Apply KISS

Repeatedly ask: is there a simpler architecture satisfying our requirements? One service instead of five. PostgreSQL instead of distributed NoSQL. GBDT instead of deep neural network. Workflow instead of agent. Single agent instead of multi-agent.

## 40. Apply YAGNI

Do not solve hypothetical requirements prematurely. No five-region active-active platform for an internal pilot. No graph neural network because graph ML sounds advanced. No multi-agent hierarchy when one workflow works.

## 41. Design Patterns

Discuss patterns only after the problem creates the need: Strategy, Factory, Adapter, Observer, Repository, State, Builder, Chain of Responsibility, Circuit Breaker, Bulkhead, Retry, Saga, Outbox.

For each important one: what problem existed? Why does this pattern help? What alternative exists? When would we avoid it?

## 42. State Diagram

When an entity has lifecycle behaviour, show it.

Payment:

```text
CREATED
  ↓
AUTHORIZED
  ↓
CAPTURED
  ├──► REFUNDED
  └──► DISPUTED
```

Agent task:

```text
CREATED
  ↓
RUNNING
  ├──► WAITING_FOR_TOOL
  ├──► WAITING_FOR_APPROVAL
  ├──► COMPLETED
  └──► FAILED
```

## 43. Security Architecture

Security is not an appendix. Cover authentication, authorization, RBAC, ABAC, ACL, tenant isolation, encryption, secret management, audit, rate limiting, network boundaries.

AI adds prompt injection, indirect prompt injection, data exfiltration, unsafe tool use, PII leakage, provider privacy, output validation.

For RAG, authorization belongs in retrieval. For agents, authorization belongs outside the LLM.

## 44. Guardrails

Think in layers:

```text
Input validation
       ↓
AuthN / AuthZ
       ↓
Retrieval permissions
       ↓
Model policies
       ↓
Tool policy
       ↓
Output validation
       ↓
Audit
```

Critical rules should preferably be deterministic.

## 45. Failure Analysis

Now deliberately break the system. What if cache fails? Database fails? Queue is delayed? Feature store times out? Model server fails? LLM provider fails? Tool fails? Agent loops? Control plane fails? Region disappears?

Then define degraded behaviour.

## 46. Resilience Patterns

Consider timeouts, bounded retries, exponential backoff, circuit breakers, bulkheads, fallback models, fallback providers, cached responses, graceful degradation, dead-letter queues, idempotency. Failure handling should be explicit on the diagram where important.

## 47. Scaling Strategy

Scale each component according to its bottleneck.

Application tier: horizontal stateless replicas. Databases: indexes → replicas → partitioning/sharding when required. Caches: cluster/shard/hot-key protection. Streams: more partitions/consumers. Model serving: replicas/batching/GPU scaling. RAG: index sharding/replicas. Agents: bounded workers/queues/workflow executors.

Don't simply say "Kubernetes will scale it." Explain what signal causes what component to scale.

## 48. Autoscaling

Discuss appropriate signals.

Traditional service: CPU, memory, RPS, concurrency, latency.
Queue worker: queue depth, oldest-message age.
Model serving: pending requests, active sequences, tokens/sec, GPU utilization, KV-cache pressure, TTFT.

Scale based on the resource actually becoming constrained.

## 49. Load Balancing and Routing

Discuss when relevant: L4 vs L7, round-robin, least-connections, weighted routing, consistent hashing, region routing, model-aware routing, tenant-aware routing, prefix/KV locality for LLMs.

## 50. Networking

Include what the system actually needs: DNS, CDN, WAF, API gateway, reverse proxy, load balancer, VPC/VNet, subnets, NAT, private endpoints, service discovery, service mesh, TLS/mTLS. Avoid adding networking infrastructure merely to make the diagram sophisticated.

## 51. Control Plane / Data Plane

When the platform is sufficiently mature, separate them:

```text
CONTROL PLANE

Models
Policies
Configuration
Deployment
Routing
Feature definitions
Agent definitions


DATA / EXECUTION PLANE

Requests
Features / Retrieval
Model / Agent
Tools
Response
```

Ask: if the control plane is unavailable, can the current data plane continue serving? Prefer yes where practical.

## 52. Management and Observability Planes

For larger platforms we may distinguish a **management plane** (tenant/admin lifecycle, provisioning, configuration, governance) from an **observability plane** (telemetry, metrics, logs, traces, evaluation signals). Only introduce the distinction if it actually helps explain the platform.

## 53. Deployment Architecture

Now answer: where does this actually run?

```text
Internet
   │
Global Load Balancer
   │
Region
   │
API Gateway
   │
Kubernetes / Managed Compute
 ┌─┼──────────┐
Pod Pod       Pod
   │
Redis / DB / Model Serving
```

Consider multiple availability zones, replicas, health checks, readiness/liveness, pod disruption, node pools, GPU pools, managed services.

## 54. Containers and Orchestration

Discuss when appropriate: Docker, Kubernetes, serverless, managed containers, VMs. For Kubernetes: deployments, services, HPA, PDB, readiness/liveness, config/secrets, GPU scheduling, node affinity. Do not choose Kubernetes automatically for tiny systems.

## 55. CI/CD

Show how code reaches production:

```text
Commit
 ↓
Tests
 ↓
Security Scan
 ↓
Build
 ↓
Artifact Registry
 ↓
Staging
 ↓
Integration / Eval
 ↓
Canary
 ↓
Production
```

For ML systems, model deployment has its own pipeline.

## 56. MLOps / LLMOps

Track versions of data, features, models, prompts, retrieval configuration, tools, agent graphs, policies.

Typical model flow: `Train → Evaluate → Register → Shadow → Canary → Production → Rollback`.

A model update should not require manually rebuilding production infrastructure.

## 57. Infrastructure as Code

For production platforms discuss Terraform, Pulumi, CloudFormation/Bicep, environment reproducibility, configuration drift, separation between application and infrastructure deployment.

## 58. Cloud Mapping

Only now map primitives onto cloud services. First: `Object Store, Queue, Stream, SQL, Cache, Kubernetes, Model Serving`. Then AWS / Azure / GCP equivalents.

The architecture should remain understandable if all cloud logos are removed.

## 59. Multi-Region Architecture

If required, discuss active-passive, active-active, global routing, data replication, home region, regional inference, conflict resolution, data residency. Ask what actually needs global consistency — usually less than people initially assume.

## 60. Disaster Recovery

Define RTO, RPO, backup strategy, cross-region recovery, restore testing. What survives complete regional failure?

## 61. Observability

Traditional: logs, metrics, traces, OpenTelemetry, dashboards, alerts. Monitor latency, traffic, errors, saturation. Then layer in AI-specific signals.

## 62. ML / AI Observability

Classical ML: feature distribution, prediction distribution, data drift, concept drift, missing features, model performance.
RAG: retrieval latency, recall, reranking quality, groundedness, citation correctness.
LLM: TTFT, inter-token latency, tokens, context size, cost.
Agent: steps/task, tool calls, tool failures, loops, completion rate, human escalations.

## 63. Distributed Tracing

A trace should follow the business request.

RAG: `Request → Auth → Retrieve → Rerank → LLM → Response`.
Agent: `Task → Agent → Tool A → Tool B → Approval → Response`.

This is much more useful than disconnected service logs.

## 64. Feedback Loop

Show how production creates future learning.

ML: `Prediction → Outcome → Label → Training`.
RAG: `Query → Result → User feedback → Retrieval evaluation`.
Agent: `Task → Trace → Outcome → Evaluation → Improve policy/prompt/tools`.

Think about delayed labels, selection bias, and feedback loops.

## 65. Cost

Identify cost drivers explicitly.

Software: compute, database, storage, egress, streaming.
ML: training, feature computation, inference replicas.
RAG: embeddings, vector storage, reranking, LLM tokens.
LLMs: GPU utilization, token generation, KV cache.
Agents: number of steps, model calls, tool calls, context growth.

Architecture should be economically sustainable.

## 66. Cost Optimizations

Caching, batching, smaller models, model routing, quantization, autoscaling, spot/preemptible training, tiered storage, context pruning, output limits, bounded agent steps. Always preserve SLO and required quality.

## 67. Architecture Evolution

This should happen throughout the interview, not only at the end. Label diagrams:

```text
V0 — simplest viable system
V1 — traffic increases
V2 — freshness / async requirements
V3 — stronger reliability
V4 — multi-tenancy
V5 — global scale
```

Each version must answer: what changed in the requirement? What broke? Why did this component fix it?

## 68. Explicit Architectural Principles Check

Near the end, mentally review: KISS (did we introduce unnecessary complexity?), YAGNI (did we solve requirements nobody asked for?), DRY (are important rules or transformations duplicated?), SOLID (are responsibilities and abstractions healthy at the LLD layer?), Separation of Concerns, Loose Coupling / High Cohesion, Fail Fast, Defence in Depth, Design for Failure.

## 69. Trade-Off Summary

Explicitly call out the major decisions:

> PostgreSQL over DynamoDB because strong uniqueness and relational access matter more than extreme write scale today.
> Hybrid retrieval over pure vector search because exact terminology matters alongside semantic similarity.
> Single agent over multi-agent because the workflow doesn't yet justify coordination overhead.
> Managed model serving over self-hosting because current traffic doesn't justify owning GPU infrastructure.

An architecture without trade-offs is probably memorized rather than designed.

## 70. Interviewer Follow-Up Round

Expect the interviewer to attack the design: What is your biggest bottleneck? What happens at 10x traffic? At 100x? Why this database? Why this cache? Why Kafka? Why an agent? Why not an agent? What happens if the model is unavailable? If the region fails? How do you prevent duplicate side effects? How do you protect tenant data? How would you cut cost in half? What would you simplify for an MVP?

The answer should refer back to design constraints rather than technology slogans.

## 71. Final Whiteboard

At the end, consolidate into one clean architecture diagram — something we could plausibly redraw during an interview. Avoid fifty cloud icons. Clearly identify the critical path, async path, major stores, intelligence layer, control plane where relevant, and failure boundaries.

The test is not "can I memorize this diagram?" It is "can I explain why every box exists?"

## 72. Final Two-Minute Interview Summary

Finish like an experienced candidate. A strong structure is:

> I started with the user-critical path and kept the serving tier stateless. The main design challenge was X, which led me to Y. I separated synchronous serving from asynchronous processing so Z cannot affect user latency. For storage I chose A because of these access patterns. The AI layer uses B because it meets our quality and latency requirements without C's operational complexity. The major failure mode is D, so we degrade through E. At the current scale this architecture is sufficient; if traffic grows by another order of magnitude, the first areas I'd revisit are F and G.

That leaves the interviewer with the architecture and the reasoning behind it.

## The Short Mental Checklist

You will not have time to consciously think through seventy-two headings during an interview. The compressed mental flow is:

**Clarify → Define Intelligence → Metrics → Estimate → Critical Path → V0 → Data → AI/ML Flow → Serving → Storage/APIs → HLD → Scale → Concurrency → LLD → Security → Failures → Deployment → Cloud → Observability → Cost → Evolve → Defend.**

For ML, emphasize: `Data → Features → Training → Serving → Feedback`.
For RAG: `Ingestion → Retrieval → Reranking → Generation → Evaluation`.
For Agentic AI: `Goal → State → Reasoning → Tools → Execution → Guardrails → Durability → Evaluation`.
For LLM infrastructure: `Traffic → Tokens → Model → Batching → GPU Capacity → Routing → Autoscaling → Reliability → Cost`.

The framework stays the same. The question decides where we spend the interview.
