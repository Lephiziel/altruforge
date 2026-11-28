# Run storage contract

`internal/store` is the local SQLite persistence boundary for orchestration. Open a store with `store.Open(path)` and close it when the owning process exits. The schema is versioned with SQLite `user_version`; migration 1 creates `runs`, `events`, and `side_effects` atomically. Newer schemas and unsupported migration paths fail closed with an error. Do not delete or recreate a database after a migration error.

## Runs and transitions

`Create` accepts a `run_<32 lowercase hex>` ID and positive time limit. It commits the identity in `created` state and its first `run.state_changed` event in one transaction. `Transition` validates states against [the run lifecycle](../spec/run-lifecycle.md) and atomically commits the new state, attempt counter, and event. Entering `implementing` increments attempts. State-changing event IDs are stable idempotency keys: replaying a committed ID does not apply another transition or append another event.

The normal path is `created → preflighting → selecting → claiming → preparing → implementing → verifying → publishing → awaiting_review`; selection can end in `no_work`, claim conflicts can return to selection, verification can request another implementation attempt, and active states can end in `paused`, `blocked`, `failed`, or `cancelled`. A paused run resumes through `preflighting`, never by silently continuing an interrupted operation. `RecoverInterrupted` transactionally marks unfinished runs paused and emits recovery state events; callers must provide a fresh recovery ID for each recovery operation.

## Events and checkpoints

`Events(ctx, runID, afterSequence)` returns committed events in increasing sequence order. Sequence allocation and event insertion share the state/checkpoint transaction. Event IDs are unique per run, so replay cannot duplicate a committed identity. Event values use schema version `0.1`, UTC timestamps, and the public event type enumeration. Event/checkpoint data must be JSON objects. The store rejects sensitive field names associated with credentials, authorization, secrets, tokens, sessions, cookies, and API keys; callers must also redact sensitive values before storage because a generic store cannot identify every secret from its value alone.

`SaveCheckpoint` atomically stores the checkpoint and a `checkpoint.saved` event. Persist a checkpoint before beginning an external operation. The checkpoint/event ID is an idempotency key.

## External side effects

Call `BeginSideEffect` before issuing an externally visible request. It commits an `intent` row keyed by a stable effect ID; only then may orchestration contact the external system. On recovery, query `SideEffects` and reconcile `intent` or `observed` records against upstream state before retrying. Advance status with `SetSideEffectStatus` to `observed` and then `complete`. An ambiguous timeout remains an intent/observed effect, not proof of failure. The store never retries external operations itself.

## Attempts and elapsed time

The attempts counter and elapsed nanoseconds survive reopen and explicit resume. Use `StartActiveInterval` / `StopActiveInterval` around each active interval; Go's monotonic clock component, not an adjustable wall-clock difference, measures elapsed time within a process. The caller persists elapsed time at checkpoints and before orderly pause/resume. A process killed between persistence points cannot yield an exact monotonic duration after restart; the store deliberately does not infer it from wall-clock timestamps. Orchestration must conservatively enforce the remaining limit when accounting for an interrupted interval. This limitation must not be treated as evidence that time-limit enforcement is complete.

## Privacy and durability

The store accepts only explicitly supplied run/event/checkpoint/effect data and has no API for credentials or provider sessions. Do not put credentials, session exports, authorization headers, or sensitive environment values in any supplied payload. SQLite transactions define the commit boundary: after a forced process exit, committed rows are recovered; uncommitted transactions are rolled back by SQLite. A committed in-flight run is not success and should be passed to `RecoverInterrupted` before explicit resume.
