# Architecture

## Shape

The reference runtime is one Go CLI with a modular core and adapters at external boundaries. The core owns the run state machine and policy decisions. It does not expose provider-specific payloads to the rest of the application.

| Port | Responsibility |
| --- | --- |
| ProjectLoader | Read a pinned manifest and instruction set; validate and hash the effective policy |
| TaskSource | Return normalized, eligible candidate tasks |
| Coordinator | Grant, renew, fence, and release task leases |
| Agent | Start, observe, interrupt, and resume supported agent work |
| Executor | Prepare and terminate the controlled execution environment |
| Verifier | Execute required checks and produce structured evidence |
| Forge | Read GitHub state, manage forks, and publish an idempotent Draft PR |
| Store | Persist transitions, checkpoints, events, and side-effect identifiers |

These are design boundaries, not generated interface stubs. Define the smallest concrete Go APIs needed in MVP-02 and the relevant adapter task.

## Authority and flow

The contributor's requested limits and the pinned project policy produce the effective run policy. The stricter limit wins. Issue text and model output cannot modify that policy.

The task lease is granted by project-controlled infrastructure. Local SQLite is never the authority for cross-machine task ownership.

The agent works on a pinned base in a dedicated workspace. Required verification and publication are separate from agent self-assessment. Publication records immutable result references before contacting GitHub so an ambiguous response can be reconciled.

A Draft PR follows successful local required checks. It remains a draft while trusted project CI and human review evaluate it. Opening a PR is not a claim that upstream checks already passed.

## Intended paths

| Path | Responsibility |
| --- | --- |
| `cmd/altruforge/` | Entry point |
| `internal/cli/` | Commands, account setup, and progress presentation |
| `internal/run/` | State machine, budgets, checkpoints, and orchestration |
| `internal/project/` | Manifest loading, validation, and policy digests |
| `internal/policy/` | Enforced task, path, and publication restrictions |
| `internal/task/` | Normalized work and discovery |
| `internal/coordinator/` | Lease client and trusted GitHub coordinator |
| `internal/agent/codex/` | Documented Codex protocol adapter |
| `internal/executor/` | Controlled execution and lifecycle |
| `internal/verify/` | Required checks and evidence |
| `internal/forge/github/` | GitHub integration |
| `internal/store/` | SQLite and migrations |
| `spec/` | Language-independent draft contracts |

These application directories are created by implementation tasks. Empty packages and placeholder implementations are deliberately absent.

## Extension model

MVP adapters are built into the binary. Future external plugins use a versioned process protocol with declared capabilities. Go shared-library plugins are excluded because of their platform and toolchain constraints.

Hooks initially consume events for notifications. They cannot override a required failed check or broaden execution permissions.

## Boundary that must be proven

[ADR 0003](adr/0003-execution-and-authentication.md) is evidence-gated. A container by itself does not prove credential separation or cross-platform agent isolation. MVP-01 must establish a supported provider integration and execution path before the product claims that boundary.

See [run lifecycle](../spec/run-lifecycle.md), [coordination](../spec/coordination.md), and [authentication](security/authentication.md).
