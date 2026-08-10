# ML System Design Interview Toolkit

This companion turns the blog's reasoning process into three reusable artifacts:

- `interview_template.md` keeps the canonical interview headings and the questions each section must answer.
- `system_contract.yaml` is an example decision-system contract. It is deliberately implementation-neutral.
- `estimation.py` converts traffic, event size, latency, and replica assumptions into a capacity envelope.

## Run the calculator

```bash
python3 estimation.py
python3 estimation.py --daily-decisions 250000000 --peak-factor 7 --event-kb 4
```

The output is JSON so it can be pasted into notes or consumed by another tool.

## Run the tests

```bash
python3 -m unittest discover -s tests
```

The package uses only the Python standard library.
