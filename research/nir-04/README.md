# NIR-04 / P0 — research design

**Status:** design and formal exploration only. The primary experiment is not authorized and has not been run.

NIR-04 studies the safety and conditional liveness boundary of autonomous publication of verified artifacts when requests can settle late, publishers race, observations are stale or unavailable, and recovery repeatedly crashes. It follows the frozen NIR-03 record without revising its classifications. The work here is a structured, reproducible literature review, a retrospective, falsifiable questions, a bounded formal extension, and a preregistration-ready experimental design.

## Current disposition

- NIR-03 archive and historical-file integrity passed an independent local audit. Live PR #29 state, remote head and CI could not be verified because GitHub was unreachable. See [P0-REVIEW.md](P0-REVIEW.md); owner acceptance is conditional on live checks.
- Literature review findings support established mechanisms and assumptions, not a novelty claim. Search coverage is documented in [LITERATURE-SEARCH-PROTOCOL.md](LITERATURE-SEARCH-PROTOCOL.md).
- Formal work is in [`formal/`](formal/). TLC availability was checked; see [REPRODUCIBILITY.md](REPRODUCIBILITY.md). No primary trial has been executed.
- The future experiment remains a proposal; its final sample size and frozen endpoint contracts must be reviewed before any primary trial.

## Documents

- [RELATED-WORK.md](RELATED-WORK.md) — selected primary literature and authoritative specifications.
- [RESEARCH-GAP-MATRIX.md](RESEARCH-GAP-MATRIX.md) — established knowledge, adaptation, open questions and tentative contribution candidates.
- [NIR-03-RETROSPECTIVE.md](NIR-03-RETROSPECTIVE.md) — interpretation without recoding prior observations.
- [RESEARCH-QUESTIONS.md](RESEARCH-QUESTIONS.md) and [HYPOTHESES.md](HYPOTHESES.md) — falsifiable questions and variables.
- [FORMAL-SPECIFICATION.md](FORMAL-SPECIFICATION.md) — extension assumptions and properties.
- [EXPERIMENTAL-PROTOCOL.md](EXPERIMENTAL-PROTOCOL.md) and [ANALYSIS-PLAN.md](ANALYSIS-PLAN.md) — design only.
- [THREATS-TO-VALIDITY.md](THREATS-TO-VALIDITY.md) — limitations and mitigations.
- [REPRODUCIBILITY.md](REPRODUCIBILITY.md) — tool availability and reproduction steps.
- [P0-REVIEW.md](P0-REVIEW.md) — NIR-03 closeout audit.

## Decision gate

This branch does not implement product behavior, alter NIR-03 evidence, run a primary experiment, merge a PR, or authorize later experimental work. The requested next decision is owner review of this design and separate approval before any primary-trial execution.
