# MVP-14 Implement cross-platform packaging and release checks

Status: not implemented.
Dependencies: [MVP-02](MVP-02.md), [MVP-13](MVP-13.md)

## Outcome

Produce tested runtime artifacts without claiming that cross-compilation proves execution support.

## Read first

- [docs/platforms.md](../../docs/platforms.md)
- [docs/release-readiness.md](../../docs/release-readiness.md)
- [docs/development.md](../../docs/development.md)

## Acceptance criteria

- [ ] Build the declared Windows/macOS/Linux binaries using pinned toolchain/dependencies.
- [ ] Execute packaging/installation smoke checks on the target OS families, including spaced/non-ASCII paths.
- [ ] Generate checksums and source revision references; document artifact provenance and actual install steps.
- [ ] Keep release permissions restricted and require the runtime readiness gate before publication.
- [ ] Keep signing/notarization status explicit; never imply a signature exists if it was not created.
- [ ] Update documentation to distinguish a target, a built artifact, and a verified runtime route.

## Out of scope

Publishing an untested installer, silent auto-update, and operating-system claims based only on build output.

## Required handoff

Artifact inventory, packaging CI results, checksums, and release readiness status.

Use [the handoff template](../agents/HANDOFF.md). All changes and reports must be in English.
