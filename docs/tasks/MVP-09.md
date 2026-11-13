# MVP-09 Implement eligible issue discovery and task selection

Status: not implemented.
Dependencies: [MVP-03](MVP-03.md), [MVP-05](MVP-05.md), [MVP-08](MVP-08.md)

## Outcome

Find eligible work, select one candidate within policy, and acquire authority before implementation.

## Read first

- [spec/project-manifest.md](../../spec/project-manifest.md)
- [spec/coordination.md](../../spec/coordination.md)
- [docs/product/mvp.md](../../docs/product/mvp.md)

## Acceptance criteria

- [ ] Require all include labels and reject any excluded label, closed issue, active lease, or existing harness PR.
- [ ] Reject or skip tasks without actionable acceptance criteria; issue text cannot broaden project policy.
- [ ] Support deterministic oldest_first selection and bounded agent ranking only among eligible candidates.
- [ ] Acquire a current lease and retry a conflict by returning to selection within the same overall budget.
- [ ] Emit a task.selected event explaining the selected scope before execution without a routine contributor confirmation.
- [ ] Return no_work clearly when no permitted task exists; do not invent an unrelated task.

## Out of scope

Autonomous roadmap expansion, a global project catalog, and file-based task-source parity.

## Required handoff

Deterministic eligibility fixtures, conflict/no-work cases, and selection-event evidence.

Use [the handoff template](../agents/HANDOFF.md). All changes and reports must be in English.
