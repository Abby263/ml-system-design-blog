# Blog folders

This directory contains one folder per blog in the **Designing ML Systems** series.

## Naming convention

Use this format:

```text
NN-short-title/
```

Examples:

```text
01-introduction/
02-url-shortener/
03-distributed-rate-limiter/
```

Each folder should contain:

- `README.md` — blog companion notes, architecture summary, and local setup.
- `assets/` — technical SVGs such as HLDs, LLDs, sequence diagrams, flowcharts, and mind maps.
- `code/` — runnable implementation, tests, load tests, deployment files, and scripts for that blog.

Introductory or conceptual posts can keep `code/README.md` as a placeholder explaining that no executable code is required.

Use diagrams to explain a concrete relationship, decision, or flow. Prefer SVG for technical visuals so labels stay exact and the source remains editable; avoid decorative stock imagery that does not teach the system.
