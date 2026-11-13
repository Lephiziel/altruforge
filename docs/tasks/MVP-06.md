# MVP-06 Implement the Codex agent adapter

Status: not implemented.
Dependencies: [MVP-01](MVP-01.md), [MVP-02](MVP-02.md), [MVP-04](MVP-04.md)

## Outcome

Provide a normalized agent interface using the supported app-server route proven by MVP-01.

## Read first

- [docs/adr/0003-execution-and-authentication.md](../../docs/adr/0003-execution-and-authentication.md)
- [docs/security/authentication.md](../../docs/security/authentication.md)
- [spec/events-and-reports.md](../../spec/events-and-reports.md)

## Acceptance criteria

- [ ] Pin/document the supported protocol subset and detect incompatible provider versions or missing required capabilities.
- [ ] Support initialization, session start, user-relevant events, completion, interruption, and explicit resume where supported.
- [ ] Handle partial/truncated/malformed messages, process death, auth errors, quota exhaustion, and cancellation without a false success.
- [ ] Keep provider-owned credentials outside worker-readable storage and never expose raw auth/session payloads or hidden reasoning.
- [ ] Persist safe provider session references separately from secrets and honor the effective run budget.
- [ ] Run adapter contract fixtures plus a separately recorded budgeted live-provider smoke.

## Out of scope

Claude parity, building a new model tool loop, and paid API fallback.

## Required handoff

Adapter contract results, supported version/capability matrix, and the exact evidence relied on from MVP-01.

Use [the handoff template](../agents/HANDOFF.md). All changes and reports must be in English.
