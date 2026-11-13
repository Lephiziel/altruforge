# MVP-13 Implement onboarding and the public CLI contract

Status: not implemented.
Dependencies: [MVP-03](MVP-03.md), [MVP-04](MVP-04.md), [MVP-05](MVP-05.md), [MVP-06](MVP-06.md), [MVP-10](MVP-10.md), [MVP-12](MVP-12.md)

## Outcome

Expose a usable first-run and recovery experience around actual implemented behavior.

## Read first

- [spec/cli.md](../../spec/cli.md)
- [docs/product/mvp.md](../../docs/product/mvp.md)
- [docs/platforms.md](../../docs/platforms.md)

## Acceptance criteria

- [ ] Implement documented commands or clearly reject unimplemented ones; keep help consistent with behavior.
- [ ] Doctor identifies missing Git, account tools, compatible agent/executor, and required capabilities before work starts.
- [ ] Auth setup uses supported flows; status/logs never expose credentials; logout respects user-owned global sessions.
- [ ] Projects can be selected locally without a mandatory hub; init produces a disabled manifest.
- [ ] JSON mode and exit codes work without a TTY; progress and final output are clear on all host OS families.
- [ ] Stop/resume/status work with persisted run IDs and reflect actual termination/hand-off state.

## Out of scope

A graphical app, installer claims without artifacts, and a central account service.

## Required handoff

CLI scenarios for first run, missing dependencies, no work, quota pause, interruption, recovery, and Draft PR handoff.

Use [the handoff template](../agents/HANDOFF.md). All changes and reports must be in English.
