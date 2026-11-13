# MVP-11 Implement independent verification and report generation

Status: not implemented.
Dependencies: [MVP-03](MVP-03.md), [MVP-07](MVP-07.md), [MVP-10](MVP-10.md)

## Outcome

Make local handoff depend on actual checks, scope compliance, and an independent review session.

## Read first

- [spec/verification.md](../../spec/verification.md)
- [spec/events-and-reports.md](../../spec/events-and-reports.md)
- [spec/schemas/run-report.schema.json](../../spec/schemas/run-report.schema.json)

## Acceptance criteria

- [ ] Evaluate changed paths against pinned policy and protect verifier configuration from the working patch.
- [ ] Run required checks in the executor and record ID, observed exit status, timeout, and pass/fail metadata.
- [ ] Block handoff when any required check fails, times out, or lacks required evidence.
- [ ] Use a fresh review context with the task/diff/evidence; a review may block but never override a failed required check.
- [ ] Generate schema-valid reports for all terminal/paused outcomes; unavailable usage remains explicitly unavailable.
- [ ] Treat local reports as contributor-controlled inputs and document trusted upstream checking separately.

## Out of scope

An LLM-only quality certificate and claims that local success means upstream CI or human review passed.

## Required handoff

Negative verifier cases, report fixtures, and command/review evidence tied to immutable references.

Use [the handoff template](../agents/HANDOFF.md). All changes and reports must be in English.
