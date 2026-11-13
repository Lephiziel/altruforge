# MVP-07 Implement the controlled Linux executor

Status: not implemented.
Dependencies: [MVP-01](MVP-01.md), [MVP-02](MVP-02.md), [MVP-03](MVP-03.md)

## Outcome

Execute project work/check commands in the proven boundary with predictable lifecycle and resources.

## Read first

- [docs/adr/0003-execution-and-authentication.md](../../docs/adr/0003-execution-and-authentication.md)
- [spec/project-manifest.md](../../spec/project-manifest.md)
- [docs/platforms.md](../../docs/platforms.md)

## Acceptance criteria

- [ ] Prepare a dedicated workspace and record an immutable resolved image digest and platform before running code.
- [ ] Use argument arrays, filtered environment, declared CPU/memory limits, and enforceable network policy.
- [ ] Do not mount host home, credentials, or the Docker daemon socket into a worker.
- [ ] Cancel and verify termination of the full job, including descendants; clean up only tool-owned resources.
- [ ] Support the documented Windows/macOS/Linux host route and fail closed when a required isolation capability is missing.
- [ ] Resume only against compatible pinned execution identity; collect bounded, redacted logs and observed command results.

## Out of scope

Native Xcode/Windows build targets, privilege escalation, and an unrestricted host fallback.

## Required handoff

Boundary/resource/cancellation integration results on the target host families and a documented executor capability contract.

Use [the handoff template](../agents/HANDOFF.md). All changes and reports must be in English.
