# MVP-01 Prove supported authentication and execution boundaries

Status: not implemented.
Dependencies: None.

## Outcome

Establish a supported Codex account/execution route for Windows, macOS, and Linux before treating the boundary as a product capability.

## Read first

- [docs/adr/0003-execution-and-authentication.md](../../docs/adr/0003-execution-and-authentication.md)
- [docs/security/authentication.md](../../docs/security/authentication.md)
- [docs/security/threat-model.md](../../docs/security/threat-model.md)
- [docs/platforms.md](../../docs/platforms.md)

## Acceptance criteria

- [ ] Record the exact provider, OS/architecture, executor, and protocol versions evaluated; distinguish observed behavior from documentation review.
- [ ] Demonstrate supported account login and a non-interactive session without extracting browser sessions or copying subscriber credentials into a worker.
- [ ] Use sentinel credentials/personal files to demonstrate that project-controlled commands and child processes cannot read protected host storage or inherited secrets.
- [ ] Demonstrate interruption of the full job and a recoverable checkpoint; identify any provider-session limitations.
- [ ] Document the actual Windows/macOS/Linux route and gaps. If a platform cannot be exercised yet, keep its gate incomplete rather than claiming success.
- [ ] Accept or amend ADR 0003 with evidence. A documented incompatibility must propose a supported alternative, not an unrestricted fallback.

## Out of scope

A production CLI, a marketplace, additional providers, and certification based only on a green unit test.

## Required handoff

A redacted evidence record in docs/evidence/MVP-01-boundary.md, environment/version matrix, and an ADR outcome. Temporary prototypes are allowed during this future implementation task; do not pass them off as the runtime.

Use [the handoff template](../agents/HANDOFF.md). All changes and reports must be in English.
