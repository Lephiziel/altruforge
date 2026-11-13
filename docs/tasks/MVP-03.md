# MVP-03 Implement strict project manifest loading and policy validation

Status: not implemented.
Dependencies: [MVP-02](MVP-02.md)

## Outcome

Load a disabled or enabled project from a pinned base and produce a validated effective policy.

## Read first

- [spec/project-manifest.md](../../spec/project-manifest.md)
- [spec/schemas/project.schema.json](../../spec/schemas/project.schema.json)
- [examples/project.yaml](../../examples/project.yaml)

## Acceptance criteria

- [ ] Reject duplicate keys, unsupported tags/aliases/merges, extra YAML documents, unknown fields, oversized/deep input, and unsupported versions.
- [ ] Disabled projects never start a contribution run.
- [ ] Resolve instruction paths within the pinned repository; reject absolute/traversal/symlink escapes.
- [ ] Enforce allowed/denied-path semantics with denial winning and protected runtime/policy paths remaining protected.
- [ ] Hash the normalized effective policy and retain source commit references; combine project/contributor limits by taking the stricter value.
- [ ] Validate runtime-only invariants beyond JSON Schema, including network configuration and duplicate check IDs.

## Out of scope

Executing checks, selecting live issues, or editing project policy in response to model text.

## Required handoff

Contract fixtures and negative cases, exact check results, and documented normalized policy semantics.

Use [the handoff template](../agents/HANDOFF.md). All changes and reports must be in English.
