# MVP-04 Implement durable run state and crash recovery

Status: implementation complete in [PR #37](https://github.com/Lephiziel/altruforge/pull/37); latest cross-platform CI is rerunning after the final attempt-limit enforcement update.
Dependencies: [MVP-02](MVP-02.md)

## Outcome

Persist state transitions, events, checkpoints, and side-effect identifiers so interruption is recoverable.

## Read first

- [spec/run-lifecycle.md](../../spec/run-lifecycle.md)
- [spec/events-and-reports.md](../../spec/events-and-reports.md)
- [docs/testing.md](../../docs/testing.md)

## Acceptance criteria

- [x] Implement the documented run identity and valid transitions, including pause, no_work, blocked, failure, and cancellation.
- [x] Use SQLite transactions/migrations and persist intent before externally visible side effects.
- [x] Allocate event sequence numbers durably and replay without duplicating committed event identities.
- [x] Reopen a store after forced termination and recover the last committed state without treating partial work as success.
- [x] Track attempts across explicit resume and elapsed intervals with Go's monotonic clock; persist accumulated elapsed time.
- [x] Reject sensitive credential/session field names, document caller redaction duties, and fail on corruption or unsupported schema versions.

## Out of scope

Distributed task authority, autonomous quota-reset wakeups, and user-facing dashboards.

## Required handoff

Crash/reopen and transition evidence, migration tests, and the storage contract available to orchestration.

Use [the handoff template](../agents/HANDOFF.md). All changes and reports must be in English.

## Implementation handoff

### Task and revision

MVP-04, [Issue #6](https://github.com/Lephiziel/altruforge/issues/6), branch `implementation/mvp-04-durable-run`, [Draft PR #37](https://github.com/Lephiziel/altruforge/pull/37).

### Resulting behavior

The `internal/store` package provides SQLite-backed run identity, lifecycle transitions, attempts, elapsed-time accumulation, checkpoints, sequenced public events, and idempotent side-effect intent/status records. `RecoverInterrupted` pauses unfinished runs and emits a recovery event; it never marks interrupted work successful. See [storage contract](../storage.md).

### Changes

- `internal/store/store.go`: schema migration, transactional run/event/checkpoint writes, transition and attempt-limit validation, recovery, side-effect reconciliation API, monotonic interval accounting, and sensitive-key rejection.
- `internal/store/store_test.go`: state/outcome paths, attempt-limit and event ordering/replay, intent/checkpoint persistence, actual subprocess termination/reopen, migration/corruption failures, and privacy checks.
- `docs/storage.md`: orchestration-facing storage and recovery contract.

### Validation

| Command or scenario | Environment | Observed result |
| --- | --- | --- |
| `go test ./internal/store -count=1` | Linux amd64, Go 1.27.4-X:nodwarf5 | PASS |
| `go test ./...` | Linux amd64, Go 1.27.4-X:nodwarf5 | PASS |
| `go vet ./...` | Linux amd64, Go 1.27.4-X:nodwarf5 | PASS |
| `go test -race ./...` | Linux amd64, Go 1.27.4-X:nodwarf5 | PASS |
| `CGO_ENABLED=0 go build ./cmd/altruforge` | Linux amd64, Go 1.27.4-X:nodwarf5 | PASS |
| Forced child-process exit after committed state/event, then reopen and recover | Linux amd64 | PASS; committed preflight state and sequence survive, recovery changes it to paused |
| `git diff --check` | Linux checkout | PASS |
| Windows/macOS local execution | Not run locally | Latest PR CI rerun pending after the attempt-limit update |

### Boundaries

The store is not wired into CLI orchestration; provider/session/workspace recovery is not implemented. In-process elapsed intervals use Go's monotonic clock and are persisted when stopped. Exact monotonic duration between the last persistence point and an abrupt process death cannot be reconstructed portably; orchestration must conservatively enforce remaining limits for that uncertainty. Sensitive field-name rejection is defense in depth, not value-based secret detection; callers must redact payload values. Three-OS CI covers Go application checks, not full product end-to-end scenarios or live providers.

### Dependency handoff

MVP-06 and MVP-10 can now depend on the `internal/store` API for durable local run state, provided they retain the documented recovery/time-accounting limitations. MVP-01's security boundary remains an independent gate.

### Review notes

No contract schema change or ADR was needed. SQLite is local persistence only and is not an authority for task leases.
