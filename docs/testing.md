# Testing strategy

Tests must demonstrate the behavior promised by the selected task and the draft contracts. Keep normal tests offline with deterministic clocks, temporary repositories, and controlled provider/forge fixtures.

| Surface | Required evidence |
| --- | --- |
| Project validation | Unknown fields/versions, malformed YAML, duplicate keys, invalid paths, incompatible capabilities, and disabled project |
| Policy | Allow/deny precedence, protected configuration, stricter combined limits, and untrusted text attempting to broaden authority |
| Store and state | Crash recovery, migration behavior, transition rules, event ordering, and replay without duplicate side effects |
| Agent adapter | Success, malformed or truncated messages, unsupported versions, interruption, quota/auth failures, and explicit resume |
| Executor | Resource limits, image pinning, workspace boundaries, environment filtering, and complete termination |
| Coordinator | Concurrent claims, CAS conflict retries, expiry, renewal, replay, stale generations, and revoked access |
| Selection | Deterministic eligibility, closed/assigned/excluded issues, missing acceptance criteria, and no eligible work |
| Verification | Required check failure, timeout, missing evidence, scope violations, and independent review findings |
| Publication | Lost response, duplicate request, existing PR reconciliation, stale lease, changed base, and immutable result references |
| CLI | Stable exit codes, JSON mode, no secret leakage, budget notification, and clean interruption |
| Platforms | Actual Windows/macOS/Linux execution, spaced/Unicode paths, and non-interactive operation |

## Layers

Unit tests cover rules and state. Adapter contract tests check capability behavior. Integration tests use real Git, SQLite, subprocesses, and the executor. End-to-end tests use a dedicated repository and account, never an unsuspecting upstream project.

Live provider tests are opt-in and budgeted. Record the provider/runtime versions and actual environment. No live evidence is claimed in this bootstrap repository.

## Evaluating contribution quality

Use a small, preselected set of real tasks with explicit acceptance criteria. Compare with the same coding tool and a similar budget. Include unsuccessful runs, review corrections, setup time, and later regressions.

For a bug fix, a regression should fail against the original behavior and pass with the fix where practical. A second model's agreement is supporting review, not proof.

## Required CI evolution

The current workflow checks documents, schemas, and examples only. MVP-02 adds real Go checks on all required OS families. Executor and live-provider evidence remain separate jobs or recorded release checks; they must not be represented by an unrelated green badge.
