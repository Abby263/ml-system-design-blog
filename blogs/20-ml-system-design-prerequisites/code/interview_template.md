# ML System Design Interview Worksheet

Use the headings in order. If one is not applicable, keep it and explain why.

## Interview Prompt

- Restate the prompt in one sentence.
- Identify the decision recipient, output, deadline, outcome, and guardrails.
- List the two or three clarifying questions that could materially change the design.

## Business Decision and Scope

- Decision contract:
  `For <recipient>, use <available evidence> to <output/action> before <deadline>, optimizing <outcome> while protecting <guardrails>.`
- Why ML instead of deterministic logic?
- In scope / explicitly out of scope:

## Functional Requirements

- Inputs and outputs:
- Decision, feedback, training, replay, explanation, and human-review behaviors:

## Non-Functional Requirements

- Latency and throughput:
- Availability and degradation:
- Freshness and consistency:
- Auditability, privacy, security, and cost:

## Intelligence Problem

- Entity/request, observation time, target, horizon, and output:
- Prediction-policy-action boundary:
- Baseline formulation:

## Success Metrics

- Business outcome:
- Decision-quality metric at the operating point:
- System-health metrics:
- Safety, fairness, privacy, and product guardrails:

## Back-of-the-Envelope Estimation

- Average and peak QPS:
- Event ingress and retained storage:
- In-flight requests and replica floor:
- Latency-budget allocation:
- Which estimate changed the architecture?

## HLD V0

- Draw the smallest complete learning loop.
- Name synchronous and asynchronous boundaries.
- State the baseline, event contract, artifact boundary, and fallback.

## Architecture Evolution

- Which measured contract failure earns each added component?
- Which component would you remove at one-tenth the scale?

## Data and Labels

- Decision, exposure, action, and outcome events:
- Point-in-time correctness and leakage prevention:
- Label delay, missing outcomes, bias, backfills, and retention:

## Features and Models

- Baseline and candidate model families:
- Feature ownership, freshness, parity, and defaults:
- Offline split, slices, calibration, and comparison to baseline:

## Online Serving and Critical Path

- Deadline propagation and dependency budget:
- Batch, online, streaming, or edge mode—and why:
- Cache, model loading, batching, idempotency, and overload behavior:

## Reliability, Security, Deployment, and Observability

- Software, data, model/decision, and business telemetry:
- Offline, replay, shadow, canary, promotion, and rollback gates:
- Fallback ladder and recovery proof:
- Threat model, access control, encryption, retention, and audit:

## LLD and Implementation

- Request/response, event, feature, model-bundle, and rollout contracts:
- Versioning and compatibility rules:
- One critical-path sequence or pseudocode sketch:

## Final Whiteboard and Two-Minute Answer

- Trace one decision from request to action and later learning.
- Name the hardest trade-off, the safe failure mode, and the next evolution trigger.

## References

- Primary papers, official documentation, and relevant company engineering posts:

## What Comes Next

- Open questions to validate after the interview:
- The next case study or experiment this design enables:
