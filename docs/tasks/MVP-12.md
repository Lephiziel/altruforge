# MVP-12 Implement idempotent Draft PR publication

Status: not implemented.
Dependencies: [MVP-05](MVP-05.md), [MVP-08](MVP-08.md), [MVP-10](MVP-10.md), [MVP-11](MVP-11.md)

## Outcome

Hand off one immutable verified result through the contributor fork without duplicate PRs on ambiguous retries.

## Read first

- [spec/coordination.md](../../spec/coordination.md)
- [spec/verification.md](../../spec/verification.md)
- [spec/run-lifecycle.md](../../spec/run-lifecycle.md)

## Acceptance criteria

- [ ] Check current lease generation, actor, base/policy, and verified result before publication.
- [ ] Persist publication intent and a stable run marker before contacting GitHub.
- [ ] Reconcile an existing fork branch/PR after a lost response; do not infer failure from a timeout.
- [ ] Use coordinator fencing and reconciliation to prevent duplicate authorized publication; test concurrent/replayed requests.
- [ ] Create a Draft PR with task, scope, checks, limitations, AI assistance, and immutable references; never enable auto-merge.
- [ ] Return awaiting_review with the actual PR link and honest upstream status, then end the active run.

## Out of scope

Merging, automatically answering review feedback, and attributing work to a pooled subscriber account.

## Required handoff

Dedicated-repository integration evidence including a lost-response scenario and observed idempotency behavior.

Use [the handoff template](../agents/HANDOFF.md). All changes and reports must be in English.
