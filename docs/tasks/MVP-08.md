# MVP-08 Implement authoritative GitHub task leases

Status: not implemented.
Dependencies: [MVP-02](MVP-02.md), [MVP-03](MVP-03.md), [MVP-05](MVP-05.md)

## Outcome

Prove and implement project-controlled task ownership with atomic updates, expiry, and fencing.

## Read first

- [spec/coordination.md](../../spec/coordination.md)
- [spec/schemas/task-lease.schema.json](../../spec/schemas/task-lease.schema.json)
- [docs/adr/0004-github-coordination.md](../../docs/adr/0004-github-coordination.md)

## Acceptance criteria

- [ ] Demonstrate the actual non-forced GitHub state-ref update behavior under concurrent sibling writes; record conflict/retry evidence.
- [ ] Bind grants to task, contributor identity, run ID, base, policy, expiry, and a monotonically increasing generation.
- [ ] Make claim/renew/release requests idempotent and enforce project-wide lease/open-PR capacity atomically.
- [ ] Reject stale generations, revoked access, forged origins, and local-clock attempts to extend authority.
- [ ] Handle issue-comment input as data in trusted coordinator code; never execute issue/PR code with a privileged token.
- [ ] Document integration permissions, deployment/version pinning, reconciliation, and expiry behavior; accept/amend ADR 0004 with evidence.

## Out of scope

A mandatory hosted Altruforge service and claims based only on reading an "assigned" comment.

## Required handoff

Concurrent integration evidence, protocol tests, and a safe opt-in target-project workflow template.

Use [the handoff template](../agents/HANDOFF.md). All changes and reports must be in English.
