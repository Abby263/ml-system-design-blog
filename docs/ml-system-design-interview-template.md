# ML System Design Interview and Blog Template

This is the baseline for every ML system-design article in this repository. Each article should recreate two things at once:

1. the conversation with an interviewer;
2. the whiteboard evolving beside that conversation.

The goal is not to display a memorized final architecture. The reader should see requirements create constraints, constraints break simple designs, and measured failures justify each new component.

This document is the required, condensed checklist. **[The full framework](ai-system-design-interview-framework.md)** it is distilled from covers 72 stages across classical ML, RAG, LLM infrastructure, and agentic systems in more depth — use it to work out which stages matter for a new article's problem, or when a specific decision (training architecture, multi-region, agent/tool boundaries, and so on) needs more detail than this checklist gives. Do not turn its 72 headings into 72 headings in a blog post; an article should read like one continuous interview, not a checklist being marched through.

The single most important requirement below is the first one: **the article must read like an actual interview transcript, not an essay with dialogue boxes dropped in for decoration.** A reader should be able to picture two people at a whiteboard.

## Required interview spine

Every classical ML system-design article should cover these stages in this order. Related stages may share a section when that improves the narrative, but they should remain visibly identifiable.

1. **Interview prompt** — preserve the original ambiguity, then resolve it through a multi-turn clarifying-questions exchange. The candidate asks several questions that would each change the architecture (what decision is being automated, what actions exist, what deadline it sits inside, what scale/geography it needs to survive); the interviewer answers each one; the candidate reacts to the answer before asking the next question. This is not a single Q&A pair and not a bullet list of "assumptions" — it is the visible negotiation that produces the assumptions. Everything that follows should read as the formal write-up of what was just established in that exchange, not a repeat of it.
2. **Business decision and scope** — identify the user, protected entity, decision, action, and deadline.
3. **Functional requirements** — describe what the system must do.
4. **Non-functional requirements** — state latency, throughput, availability, consistency, privacy, audit, regional, and cost constraints that matter.
5. **Intelligence problem** — ask directly which parts of the system actually need a learned model versus a deterministic rule, then separate what the model predicts from what business policy decides. Treat "which parts need intelligence?" as a real question in the dialogue, not an assumption the candidate silently makes.
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

## Canonical H2 contract

Every ML system-design blog must use the following H2 headings, in exactly this order and with exactly this wording. Problem-specific explorations belong under H3 or H4 headings. Do not rename an H2 to make it sound specific to the problem; specificity belongs inside the section.

```text
## Interview Prompt
## Business Decision and Scope
## Functional Requirements
## Non-Functional Requirements
## Intelligence Problem
## Success Metrics
## Back-of-the-Envelope Estimation
## HLD V0
## Architecture Evolution
## Data and Labels
## Features and Models
## Online Serving and Critical Path
## Reliability, Security, Deployment, and Observability
## LLD and Implementation
## Final Whiteboard and Two-Minute Answer
## References
## What Comes Next
```

The first fifteen headings are the interview spine. `References` and `What Comes Next` are the common publishing appendix. No additional H2 headings should be introduced in an ML system-design blog.

If a topic is not applicable, **keep the H2** and make the applicability decision explicit. State:

1. why the concern does not affect this system under the current requirements;
2. what simpler design follows from that fact;
3. which requirement or scale trigger would make it applicable later.

For example, a single-region internal model may still include `## Reliability, Security, Deployment, and Observability`, with an H3 explaining why multi-region failover is not justified today and which residency or recovery requirement would change that decision. “Not applicable” is a defended architecture choice, not permission to omit the section.

## Write it as an interview

The blog should feel like an actual interview has been transcribed and lightly cleaned up — not a conventional article that occasionally quotes two people. Two things make dialogue read as transcribed rather than staged:

- **Real exchanges have friction.** The interviewer sometimes pushes back, asks "why not X instead," or only half-answers before the candidate asks a follow-up. A clarifying-questions exchange should be several turns long, with the candidate's next question genuinely depending on the previous answer — not a list of questions asked in a vacuum and answered in one shot.
- **The candidate reasons out loud.** Prefer "That rules out X, which means..." over restating the fact and moving on. The reader should be able to tell *why* an answer mattered, in the candidate's own words, not just that it was given.

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

State trade-offs as explicit comparisons, not adjectives. Not:

> Redis is fast.

But:

> Local caching gives us lower latency, but Redis gives the entire service fleet a shared cache. Given that mappings are frequently reused across replicas, I'll take the network hop for better consistency and shared utilization.

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
- [ ] That ambiguity is resolved through a multi-turn clarifying-questions exchange, not a single Q&A or a prose list of assumptions.
- [ ] "Which parts of this need a learned model?" is asked as a real question, not assumed.
- [ ] Business, functional, and non-functional requirements are explicit.
- [ ] Major trade-offs are phrased as explicit comparisons ("X over Y because Z"), not adjectives ("X is fast").
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
