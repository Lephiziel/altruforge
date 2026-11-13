# MVP-04 Implement durable run state and crash recovery

Status: not implemented.
Dependencies: [MVP-02](MVP-02.md)

## Outcome

Persist state transitions, events, checkpoints, and side-effect identifiers so interruption is recoverable.

## Read first

- [spec/run-lifecycle.md](../../spec/run-lifecycle.md)
- [spec/events-and-reports.md](../../spec/events-and-reports.md)
- [docs/testing.md](../../docs/testing.md)

## Acceptance criteria

- [ ] Implement the documented run identity and valid transitions, including pause, no_work, blocked, failure, and cancellation.
- [ ] Use SQLite transactions/migrations and persist intent before externally visible side effects.
- [ ] Allocate event sequence numbers durably and replay without duplicating committed event identities.
- [ ] Reopen a store after forced termination and recover the last committed state without treating partial work as success.
- [ ] Track attempts and elapsed execution consistently across explicit resume and clock adjustments.
- [ ] Keep credentials/session exports out of state and implement meaningful corruption/migration failure behavior.

## Out of scope

Distributed task authority, autonomous quota-reset wakeups, and user-facing dashboards.

## Required handoff

Crash/reopen and transition evidence, migration tests, and the storage contract available to orchestration.

Use [the handoff template](../agents/HANDOFF.md). All changes and reports must be in English.
