# Run lifecycle

## States

| State | Meaning |
| --- | --- |
| `created` | Durable run identity and requested limits exist |
| `preflighting` | Accounts, versions, configuration, and executor are checked |
| `selecting` | Eligible tasks are being evaluated |
| `claiming` | A task lease is requested from the authoritative coordinator |
| `preparing` | Base, policy, workspace, and image are pinned |
| `implementing` | The agent works within the selected task |
| `verifying` | Required checks, scope, and review are evaluated |
| `publishing` | A verified immutable result is being handed off |
| `awaiting_review` | A Draft PR exists; the active run has ended |
| `paused` | An explicit recoverable checkpoint exists; no autonomous work continues |
| `no_work` | No eligible task was found; the active run has ended |
| `blocked` | A required capability, permission, policy condition, or prerequisite is absent |
| `failed` | The run cannot complete within its policy/budget |
| `cancelled` | The contributor stopped the run and its work has terminated |

The happy path follows the table from `created` to `awaiting_review`. Selection can end in `no_work`. A lease conflict returns to selection within budget. Verification may return to implementation only while an attempt remains.

Blocking or failure is possible from any active state. Cancellation must terminate the complete job. `paused` requires explicit resume; it is not an automatic retry loop.

## Invariants

Persist a checkpoint before an externally visible operation. On recovery, reconcile the operation's observed upstream state before retrying it. A timeout is not proof that publication failed.

Use a stable `run_<32 lowercase hex characters>` identifier. Count every implementation attempt. Time limits apply across recovery; use a monotonic timer for active execution and persisted accounting rather than trusting adjustable wall-clock deltas alone.

A resumed run must revalidate policy, base, executor identity, credentials, and lease authorization. A changed base/policy or incompatible provider session must not silently continue as the previous run.

Never start a second task to hide failure of the first. Release/expire the lease and preserve the observed result.

## Handoff semantics

`awaiting_review` means a Draft PR was handed off, not that it was merged or that upstream CI passed. Upstream status may be pending. The MVP does not automatically respond to review comments or merge the PR.

Every other terminal or paused outcome explains why work stopped and whether a PR exists.
