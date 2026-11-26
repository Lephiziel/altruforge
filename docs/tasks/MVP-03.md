# MVP-03 Implement strict project manifest loading and policy validation

Status: partial implementation proposed; lexical foundation only, unverified.
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

## Task and revision

MVP-03, [issue #5](https://github.com/Lephiziel/altruforge/issues/5).
Candidate patch against base `39db8b4a2e474a09618306d1a69893b0482c5cd1`.
No result commit or branch was created in this response.
Issue #5 and MVP-03 remain incomplete.

## Resulting behavior

The proposed pure lexical API validates repository-relative paths and patterns,
then matches full paths with case-sensitive literal segments and wildcards.
A path must match an allow and no deny. Every supplied pattern is validated
before evaluation; invalid input returns false and an error even after an
earlier matching pattern. Protected denials must be supplied by the caller.
This does not establish protected-path policy integration.

## Changes

- Add standard-library-only helpers in `internal/manifest/paths.go`.
- Add table-driven positive and negative tests in `internal/manifest/paths_test.go`.
- Preserve module metadata, dependencies, public contracts, and policy fixtures.

Validation rejects empty paths, invalid UTF-8, NUL, backslashes, colons,
absolute/UNC forms, empty segments, and dot or parent components. Inputs are
never cleaned. Rejecting colons throughout also excludes Windows drive-relative
and alternate-stream forms, independently of the host OS.

A `*` matches zero or more bytes within one segment. A whole-segment `**`
matches zero or more complete segments: `docs/**` matches `docs` and
`docs/a/b`; `a/**/b` matches `a/b` and `a/x/y/b`. Embedded double stars are
rejected. Question marks, brackets, and braces are literals, without escaping,
character classes, or alternation. Matching does not normalize Unicode,
case, or separators. Paths describe lexical names, without checking existence
or distinguishing files from directories.

## Validation

No commands were executed: the task explicitly required a JSON patch without
tools. All checks below are **not run**, with no passing results claimed.
The supplied environment identifies a zsh workspace at
`/tmp/findrail-local-run-11196fca-zjypylqc/candidate` dated 2026-11-23.
Host OS, Go version, tool versions, and installed dependencies were not observed.
Prior bootstrap evidence does not validate this candidate.

| Command or scenario | Environment | Observed result |
| --- | --- | --- |
| `go mod download` | Not inspected | Not run |
| `go vet ./...` | Not inspected | Not run |
| `go test ./...` | Not inspected | Not run |
| `go test -race ./...` | Not inspected | Not run |
| `go build -o /worktmp/altruforge ./cmd/altruforge` | Not inspected | Not run |
| `altruforge-gofmt-check` | Not inspected | Not run |
| `markdownlint-cli2 **/*.md` | Not inspected | Not run |
| `check-jsonschema --check-metaschema spec/schemas/event.schema.json spec/schemas/project.schema.json spec/schemas/run-report.schema.json spec/schemas/task-lease.schema.json` | Not inspected | Not run |
| `check-jsonschema --schemafile spec/schemas/project.schema.json examples/project.yaml .altruforge/project.yaml` | Not inspected | Not run |
| `check-jsonschema --schemafile spec/schemas/run-report.schema.json examples/run-report.json` | Not inspected | Not run |
| `check-jsonschema --schemafile spec/schemas/event.schema.json examples/event.json` | Not inspected | Not run |
| `check-jsonschema --schemafile spec/schemas/task-lease.schema.json examples/task-lease.json` | Not inspected | Not run |

## Boundaries

All six whole-task acceptance items remain incomplete. Manifest loading, YAML
validation, disabled-project behavior, pinned instruction loading, symlink
confinement, protected-path integration, policy hashing, stricter-limit
combination, and runtime-only invariants remain outstanding.

This helper neither accesses a filesystem nor provides filesystem confinement.
Native Linux, Windows, and macOS execution evidence is pending. Later Linux
local checks cannot establish native Windows/macOS results. Remote CI and
upstream acceptance remain pending independently of local verification.

## Dependency handoff

No dependent whole-task gate becomes unblocked by this patch. MVP-07, MVP-08,
MVP-09, MVP-11, and MVP-13 remain blocked on complete MVP-03 evidence and their
other dependencies. The supplied MVP-02 metadata establishes module context,
not acceptance of this candidate or completion of MVP-03.

## Review notes

The selected scope uses `internal/manifest` for lexical helpers without
implementing the broader loader. No ADR or normative contract change is proposed.
Before local acceptance, all 12 mandatory checks must pass on the exact
candidate, and independent review must assess that candidate and its evidence.
Neither verification nor independent review occurred in this response.
