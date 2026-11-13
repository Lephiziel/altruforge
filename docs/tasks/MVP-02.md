# MVP-02 Bootstrap the Go module and core development workflow

Status: not implemented.
Dependencies: None.

## Outcome

Create the actual Go development foundation without assuming that the provider/execution boundary is already proven.

## Read first

- [docs/adr/0001-reference-runtime.md](../../docs/adr/0001-reference-runtime.md)
- [docs/development.md](../../docs/development.md)
- [docs/architecture.md](../../docs/architecture.md)

## Acceptance criteria

- [ ] Initialize the Go module as github.com/Lephiziel/altruforge and pin a supported stable toolchain.
- [ ] Introduce the smallest useful CLI/core structure and dependency versions; use Cobra and the selected storage approach without speculative frameworks.
- [ ] Establish real formatting, vet, tests, build, and appropriate race checks; run the application checks on Windows, macOS, and Linux CI.
- [ ] Keep the existing documentation/contract checks active and independent from runtime CI.
- [ ] Define small ports for actual external dependencies and document commands that genuinely run in the checkout.
- [ ] Do not claim sandbox/login compatibility or add a fake success path for unimplemented commands.

## Out of scope

Complete adapters, provider credentials, distributed services, and empty abstractions for every possible future feature.

## Required handoff

A buildable module, reproducible development commands, and real CI URLs. This task may proceed while MVP-01 is gathering evidence, but cannot close that gate.

Use [the handoff template](../agents/HANDOFF.md). All changes and reports must be in English.
