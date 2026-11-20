# MVP-02 Bootstrap the Go module and core development workflow

Status: partial bootstrap proposed; dependency metadata and validation pending.
Dependencies: None for proposing the bootstrap. MVP-01 evidence remains independent.

## Outcome

Create the actual Go development foundation without assuming that the provider/execution boundary is already proven.

## Read first

- [docs/adr/0001-reference-runtime.md](../../docs/adr/0001-reference-runtime.md)
- [docs/development.md](../../docs/development.md)
- [docs/architecture.md](../../docs/architecture.md)

## Acceptance criteria

- [ ] Initialize github.com/Lephiziel/altruforge with Go 1.27.3 and complete verified dependency checksums.
- [ ] Validate the minimal Cobra command and pinned SQLite dependency without speculative frameworks.
- [ ] Demonstrate help-output error propagation and regression sensitivity.
- [ ] Validate a real SQLite persistence round trip in a Unicode/spaced path.
- [ ] Pass all 12 mandatory local checks on the immutable candidate with trusted execution records.
- [ ] Obtain independent review of code, tests, scope, CI, and all mandatory outcomes.
- [ ] Obtain actual application CI execution URLs for Windows, macOS, and Linux.
- [ ] Preserve the independent documentation and contract workflow.
- [ ] Complete the English handoff against the repository handoff template.
- [ ] Keep MVP-01 and dependent task evidence explicitly unproven.

## Out of scope

Complete adapters, credentials, distributed services, runtime orchestration, storage migrations, and speculative abstractions.

## Provisional handoff

Changes: a minimal command with explicit output writers, help and rejection tests, a real SQLite persistence test, pinned direct dependencies, and an independent three-platform application workflow are proposed.

Validation: no commands were executed. There are no passing local results, tested Linux architecture, executor identity, regression experiment results, or CI URLs to report. The supplied source set did not include the handoff template; conformity to that template remains unverified.

Remaining work: generate complete dependency metadata with the trusted offline executor; run and record all 12 mandatory checks against the immutable candidate; demonstrate the regression test fails with ignored help errors; obtain independent review and real application CI results on all three platforms. The workflow intentionally rejects missing or modified dependency metadata.

Issue #4 and full MVP-02 completion remain pending. The prior candidate 3efdb8367526c06494becc44f82f6f5ef7abba66 supplies no accepted evidence for this proposal. No dependent task becomes unblocked. MVP-01 security, supported login, isolation, cancellation, and recovery remain unproven.
