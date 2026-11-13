# ADR 0001 Go reference runtime

Status: accepted.
Date: 2026-11-13.

## Context

The product is a local harness that supervises long-running external agents, maintains checkpoints, controls execution, and publishes contributions. Windows, macOS, and Linux are public MVP requirements. The specification must remain language-independent.

## Decision

Use Go for the reference CLI and core. Use Cobra for commands, SQLite through `database/sql` and `modernc.org/sqlite` for local state, and adapters around documented external protocols. Pin a supported stable Go toolchain and dependency versions in MVP-02.

The CLI is distributed as platform binaries. Agents, Git, and the executor remain external dependencies; this is not a promise that the full workflow has no installation prerequisites.

Do not use the Go shared-library plugin mechanism. Future external plugins use a versioned process boundary.

## Alternatives

TypeScript offers official Codex and Claude Agent SDK integration and a convenient path to a web client. It is the strongest alternative. Its SDK advantage does not remove platform-specific process management, credential separation, or executor requirements.

Python also has agent SDKs and is convenient for experiments, but changes the chosen distribution model. Rust is well suited to native tooling, but its additional development complexity is not justified by an established requirement of this core.

These are engineering tradeoffs, not benchmark results.

## Consequences

We own the adapter protocol types, capability negotiation, compatibility tests, and OS-specific lifecycle handling. Release builds should avoid a CGO dependency; race tests can use a different supported build configuration.

Go does not make a model produce better patches and does not establish an isolation boundary by itself.

## Evidence and reconsideration

The [technical references](../../spec/references.md) document supported protocol access and platform caveats. MVP-01 must prove the end-to-end boundary. Revisit the language only for a concrete incompatibility or measured integration/maintenance advantage, recorded in a new ADR.
