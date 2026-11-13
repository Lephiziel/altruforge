# MVP-10 Implement bounded run orchestration

Status: not implemented.
Dependencies: [MVP-04](MVP-04.md), [MVP-06](MVP-06.md), [MVP-07](MVP-07.md), [MVP-09](MVP-09.md)

## Outcome

Connect selection, preparation, implementation, verification, pause, and recovery through the core state machine.

## Read first

- [spec/run-lifecycle.md](../../spec/run-lifecycle.md)
- [docs/product/mvp.md](../../docs/product/mvp.md)
- [docs/security/threat-model.md](../../docs/security/threat-model.md)

## Acceptance criteria

- [ ] Drive only valid state transitions and persist checkpoints before operations with external effects.
- [ ] Announce the task and effective limits, then work autonomously inside that scope.
- [ ] Enforce the stricter project/contributor time and attempt budget across retries and explicit resume.
- [ ] Keep a run attached to one selected task; do not hide failure by silently starting another.
- [ ] Stop or pause on quota/auth/capability failures, cancel full execution, and preserve a useful outcome.
- [ ] Revalidate base, policy, lease generation, provider session, and executor identity on resume.

## Out of scope

Automatic merging, unbounded repair loops, and automatic wakeup after quota reset.

## Required handoff

Integration scenarios for the happy path, budget exhaustion, interruption, crash recovery, and changed policy/base.

Use [the handoff template](../agents/HANDOFF.md). All changes and reports must be in English.
