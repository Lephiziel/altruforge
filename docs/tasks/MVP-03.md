# MVP-03 Implement strict project manifest loading and policy validation

Status: implemented in [Draft PR #36](https://github.com/Lephiziel/altruforge/pull/36) pending review and merge.
Dependencies: [MVP-02](MVP-02.md)

## Outcome

Load a disabled or enabled project from a pinned base and produce a validated effective policy.

## Read first

- [spec/project-manifest.md](../../spec/project-manifest.md)
- [spec/schemas/project.schema.json](../../spec/schemas/project.schema.json)
- [examples/project.yaml](../../examples/project.yaml)

## Acceptance criteria

- [x] Reject duplicate keys, unsupported tags/aliases/merges, extra YAML documents, unknown fields, oversized/deep input, and unsupported versions.
- [x] Disabled projects never start a contribution run.
- [x] Resolve instruction paths within the pinned repository; reject absolute/traversal/symlink escapes.
- [x] Enforce allowed/denied-path semantics with denial winning and protected runtime/policy paths remaining protected.
- [x] Hash the normalized effective policy and retain source commit references; combine project/contributor limits by taking the stricter value.
- [x] Validate runtime-only invariants beyond JSON Schema, including network configuration and duplicate check IDs.

## Out of scope

Executing checks, selecting live issues, or editing project policy in response to model text.

## Required handoff

Contract fixtures and negative cases, exact check results, and documented normalized policy semantics.

Use [the handoff template](../agents/HANDOFF.md). All changes and reports must be in English.

## Normalized policy semantics

`manifest.Load` accepts one YAML document (up to 1 MiB and 64 nested levels), rejects aliases, anchors, tags, merge keys, duplicate/unknown/missing fields, and validates draft 0.1 runtime invariants. It reads instruction files through the supplied checked-out pinned base and prevents symlinks from resolving outside that repository. The caller must ensure `repoRoot` is the requested immutable base; the returned `BaseCommit` records that reference.

Effective policy hashing uses JSON encoding of the typed manifest, instruction contents, and base commit. Set-like labels, path patterns, and network hosts are sorted before hashing. Project duration and attempts are each reduced to the positive contributor limit when it is stricter; zero means no additional contributor restriction. `PathPolicy.Allowed` requires an allow match and no deny match. Denials and built-in protected path rules always win. Matching treats `*` as one segment and `**` as zero or more segments. Disabled manifests remain loadable for validation but `CanStartContribution` is false.

## Handoff

- Task: MVP-03, [Issue #5](https://github.com/Lephiziel/altruforge/issues/5).
- Package: `internal/manifest`; dependency: pinned `gopkg.in/yaml.v3` for syntax-tree inspection and strict decoding.
- Validation: see the PR check results and local command table in the PR description.
- Boundaries: no run orchestration, check execution, live issue selection, or project self-modification is included. The package validates a caller-designated pinned checkout; it does not fetch Git commits itself.
- Dependency handoff: MVP-07, MVP-08, MVP-09, MVP-11, and MVP-13 can consume the validated policy contract, subject to their other gates. MVP-01 remains a separate security gate.
