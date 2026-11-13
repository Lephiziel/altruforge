# ADR 0002 Independent specification and permissive licensing

Status: accepted.
Date: 2026-11-13.

## Context

Repositories should be able to opt in without depending on a mandatory global service. Independent harness implementations should be possible.

## Decision

Publish draft contracts, JSON Schemas, fixtures, and semantics separately from the Go implementation. Begin at draft 0.1. Stabilize only after several different repositories and toolchains have exercised the contract.

Use Apache-2.0 for the reference implementation, schemas, and project documentation. Preserve required notices for third-party materials.

## Alternatives and consequences

Copyleft would impose different source-disclosure obligations on covered modified versions. The selected priority is broad reuse, including commercial and closed derivatives under the license terms.

The harness license does not automatically license output submitted to another project. Contributions must follow the target project's licensing and contributor policies.

A stable 1.0 commitment requires explicit migration and compatibility rules. We do not claim that all current coding agents implement this draft.
