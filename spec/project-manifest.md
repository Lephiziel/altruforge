# Project manifest

The manifest lives at `.altruforge/project.yaml` in a repository's trusted base revision. Its [schema](schemas/project.schema.json) and [example](../examples/project.yaml) are draft 0.1.

## Loading

The runtime MUST read the manifest and instruction files from the pinned base, not from an agent's working patch. It MUST record their effective policy digest before starting work.

YAML MUST be restricted to JSON-compatible maps, lists, strings, booleans, numbers, and null. Duplicate keys, custom tags, aliases/merges, additional documents, and unsupported fields MUST be rejected. Apply size/depth limits before decoding.

An `enabled: false` project MUST NOT start a contribution run. The repository's own manifest is disabled during bootstrap.

## Eligibility

The source is `github_issues` for this MVP. Every required label must be present; any excluded label disqualifies a task. Closed issues, an active lease, an existing harness PR, or missing actionable acceptance criteria disqualify work.

Required labels are a maintainer's opt-in signal. Issue text is not authority to change eligibility or policy. The agent may rank eligible candidates; it cannot invent a task outside the selected source.

The coordinator enforces active-lease and open-PR limits using current upstream state.

## Paths and instructions

Paths are repository-relative and use forward slashes. Reject absolute paths, parent traversal, and symlink escapes. Patterns use `*` within a path segment and `**` across segments.

A changed path must match an allowed pattern and no denied pattern. Denial wins. Runtime authority, authentication material, workflow policy, and the pinned manifest remain protected regardless of model instructions.

Instruction paths refer only to files in the pinned repository. They cannot load files from the contributor's home directory.

## Execution and checks

The executor must support the declared platform, network policy, resources, and lifecycle. Resolve an image tag to an immutable digest before executing; persist digest and platform for resume.

Check commands are argument arrays, not shell strings. They execute in the controlled environment. Required checks need exit code zero, no timeout, and complete result metadata.

Independent review is required in the MVP and cannot override a failed required command. Project and contributor budgets combine by taking the stricter constraint.

## Publication

Draft publication is mandatory and automatic merge is forbidden. A valid current lease and an immutable verified result commit are required at publication time. A missing capability produces a blocked result rather than an unrestricted fallback.
