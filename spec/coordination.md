# Task coordination

The [lease schema](schemas/task-lease.schema.json) defines the public shape of a lease record. A copied JSON object is not authorization; the client must validate its authoritative origin and current state.

## Grant and fencing

A task is identified as `github:<owner>/<repository>#<issue-number>`. Each grant binds the task, contributor identity, run ID, pinned policy/base, expiry, and a monotonically increasing generation.

The coordinator MUST grant at most one current lease for a task. It MUST also enforce project-wide active-run and open-PR capacity. Conditional state updates or an equivalent atomic mechanism are required.

Every request has an idempotency identity. Replaying a successful claim or renewal MUST return its existing result, not increment a new generation accidentally.

## Expiry and renewal

The coordinator is the authority for expiry. A contributor's local clock cannot extend a lease. A live runner renews while authorized and stops requesting work when renewal fails.

After loss of contact, expiry, revocation, or explicit pause, the runner MUST obtain current authority before publishing or resuming. A new generation fences older workers.

A lease cannot physically stop an offline machine. It controls which result may be accepted as an authorized harness handoff.

## Publication reconciliation

Publication authorization checks task generation, run identity, policy/base, and verified result commit. Use a stable run marker in PR metadata and reconcile existing PRs before retrying.

GitHub PR creation has no general client-supplied exactly-once key. The implementation must combine coordinator reservation, deterministic run identity, and upstream reconciliation, including ambiguous responses. Do not claim exactly-once behavior from a single request.

## GitHub backend candidate

[ADR 0004](../docs/adr/0004-github-coordination.md) proposes a trusted issue-comment workflow and non-forced state-branch updates. It requires concurrent integration evidence in MVP-08. No privileged workflow is activated by this bootstrap.
