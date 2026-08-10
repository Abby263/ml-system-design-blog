# ML System Design Interview and Blog Template

This is the baseline for every ML system-design article in this repository. Each article should recreate two things at once:

1. the conversation with an interviewer;
2. the whiteboard evolving beside that conversation.

The goal is not to display a memorized final architecture. The reader should see requirements create constraints, constraints break simple designs, and measured failures justify each new component.

## Required interview spine

Every classical ML system-design article should cover these stages in this order. Related stages may share a section when that improves the narrative, but they should remain visibly identifiable.

1. **Interview prompt** — preserve the original ambiguity.
2. **Business decision and scope** — identify the user, protected entity, decision, action, and deadline.
3. **Functional requirements** — describe what the system must do.
4. **Non-functional requirements** — state latency, throughput, availability, consistency, privacy, audit, regional, and cost constraints that matter.
5. **Intelligence problem** — separate what the model predicts from what business policy decides.
6. **Success metrics** — connect business, ML, system, and operational metrics.
7. **Back-of-the-envelope estimation** — calculate only numbers that influence architecture.
8. **HLD V0** — draw the smallest system that could work.
9. **Architecture evolution** — introduce HLD V1, V2, and later versions only when a requirement or measured failure breaks the prior version.
10. **Data and labels** — define events, outcomes, bias, leakage, retention, and feedback.
11. **Features and models** — compare a baseline, chosen approach, rejected alternatives, serving constraints, and evaluation.
12. **Online serving and critical path** — show exactly what the user waits for and what proceeds in the background.
13. **Reliability, security, deployment, and observability** — make degraded behavior and trust boundaries concrete.
14. **LLD and implementation** — connect service boundaries to contracts, interfaces, concurrency, state, and code.
15. **Final whiteboard and two-minute answer** — summarize the architecture, key choices, trade-offs, failure risks, and next scaling trigger.

## Write it as an interview

Use short dialogue callouts at consequential decision points:

```html
<aside class="interview-dialogue">
  <p><strong>Interviewer</strong> What do you mean by asynchronous here?</p>
  <p><strong>Candidate</strong> The payment does not wait for that work. We durably record an event, return the authorization decision, and let a worker process the event later.</p>
</aside>
```

The candidate should sound like a strong architect: direct, technically precise, and honest about assumptions. The interviewer should probe fundamentals rather than manufacture conflict. Useful probes include:

- What does that term mean in plain language?
- Why does this requirement justify that component?
- What simpler alternative did you reject, and why?
- What happens if the dependency is slow, unavailable, duplicated, or stale?
- Which consistency guarantee is actually required?
- What metric would tell you that this design must evolve?
- When would you *not* use the pattern you just named?

Do not turn every paragraph into dialogue. Use a callout when a real interviewer would pause on a term, assumption, trade-off, or failure mode.

## Define technical terms at first use

Never rely on prestige vocabulary. When a consequential term first appears, provide:

1. a one-sentence plain-language definition;
2. what it means in this specific system;
3. why it was selected over the simplest credible alternative;
4. its important failure mode or limitation.

For example:

> A gradient-boosted decision tree is an ensemble of small decision trees trained sequentially, where each new tree reduces errors left by the current ensemble. We choose it here because the input is heterogeneous tabular data and CPU latency is tight; we would revisit the choice if long behavioral sequences or learned media representations provide measured incremental value.

Terms that commonly require this treatment include synchronous/asynchronous, idempotency, p99, calibration, point-in-time correctness, event time, watermark, online/offline features, embedding, retrieval, ranking, shadow release, canary, circuit breaker, outbox, control plane, data plane, regional cell, RTO, and RPO.

## Evolve the whiteboard with the reasoning

Do not reveal the final architecture in the opening. A typical progression is:

```text
HLD V0 — request -> one ML-aware service -> decision
HLD V1 — add historical/online features when request-only evidence fails
HLD V2 — add streaming state when batch freshness fails
HLD V3 — separate training and serving when release independence fails
HLD V4 — add explicit fallback and observability when dependencies fail
HLD V5 — add regional cells when global scale or residency requires them
```

Use solid arrows for synchronous request work and dashed arrows for asynchronous/background work. Explain the notation the first time. Every box must answer: which requirement created it, who owns it, what happens when it fails, and what evidence would let us remove or split it?

## Choose diagrams that earn their place

The problem determines the diagram set. Do not include every view merely because it exists in this template.

Commonly useful views are:

- requirements canvas;
- HLD V0, evolution steps, and final whiteboard;
- critical-path and latency diagram;
- data-flow and ML training/serving loop;
- API and sequence diagram;
- ER or database access-pattern diagram;
- component and class/UML diagram;
- state and concurrency diagram;
- control-plane/data-plane diagram;
- reliability/fallback and security/trust-boundary diagram;
- deployment topology and cloud mapping;
- observability flow.

Classical ML articles should normally include an offline-training/online-serving view. RAG articles should separate ingestion from query serving. Agentic-system articles should distinguish agents, deterministic workflow nodes, tools, sub-agents, state, and human approval.

## Explain architecture decisions, not product names

For each major choice, cover:

```text
Problem -> simplest credible option -> selected option -> why it fits now
        -> rejected alternative -> failure mode -> trigger to revisit
```

Access patterns come before database products. Vendor-neutral architecture comes before cloud mapping. Microservices require a measurable ownership, scaling, runtime, or failure-isolation boundary. Apply SOLID, DRY, KISS, YAGNI, and design patterns only where they explain a real decision:

- **SOLID:** show the interface or responsibility that benefits.
- **DRY:** eliminate duplicated knowledge such as separate training and serving feature logic.
- **KISS:** prefer the smallest design meeting current SLOs.
- **YAGNI:** name the attractive feature the requirements do not justify yet.
- **Patterns:** state the problem, alternative, benefit, and when not to use the pattern.

## Test understanding after each major section

Each meaningful H2 should end with one scenario-based knowledge check. Questions should test a decision or failure mode, not vocabulary recall. Every option needs specific feedback, followed by the best-answer explanation and one interviewer follow-up.

A strong question asks the reader to choose under constraints—for example, what to do when a feature store times out—not to expand an acronym.

## Completion checklist

Before publication, verify:

- [ ] The article begins with an ambiguous interview prompt, not a final architecture.
- [ ] Business, functional, and non-functional requirements are explicit.
- [ ] Back-of-the-envelope numbers trace to later design choices.
- [ ] Model prediction is separated from business policy/action.
- [ ] Consequential technical terms are defined at first use.
- [ ] Interviewer probes test fundamentals and trade-offs.
- [ ] HLD versions evolve only when the previous design reaches a measured limit.
- [ ] Synchronous and asynchronous paths are visually distinct.
- [ ] Data, labels, temporal leakage, training, serving, and feedback are covered.
- [ ] APIs, state, concurrency, retries, idempotency, and failure behavior are concrete.
- [ ] Security, privacy, deployment, scaling, observability, and recovery are addressed where relevant.
- [ ] Cloud products annotate a vendor-neutral design rather than replace it.
- [ ] Code snippets and companion code agree with the article contracts.
- [ ] MCQs are conceptual, interactive, and section-aligned.
- [ ] The final two-minute answer names choices, trade-offs, risks, and scaling triggers.
- [ ] Build, links, SVGs, dark mode, mobile UI, TOC, audio mode, and quiz interactions pass.
