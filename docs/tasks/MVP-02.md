# MVP-02 Bootstrap the Go module and core development workflow

Status: validated in [Draft PR #20](https://github.com/Lephiziel/altruforge/pull/20); not merged into remote `main`. [Issue #4](https://github.com/Lephiziel/altruforge/issues/4) remains open pending maintainer acceptance.

Dependencies: No prerequisite for the bootstrap itself. MVP-01 security and runtime-boundary evidence remains a separate unproven gate.

## Outcome

Provide a buildable Go module, minimal Cobra CLI, real SQLite regression coverage, and Windows/macOS/Linux application CI without claiming the provider or executor runtime has been implemented.

## Read first

- [Runtime ADR](../adr/0001-reference-runtime.md)
- [Development guide](../development.md)
- [Architecture](../architecture.md)
- [Task handoff template](../agents/HANDOFF.md)

## Acceptance criteria

These are verified against the approved source candidate, not against an upstream release:

- [x] Initialize `github.com/Lephiziel/altruforge`, pin Go 1.27.3, and check dependency metadata.
- [x] Provide a minimal Cobra command and pinned SQLite driver.
- [x] Verify help-writer error propagation and demonstrate regression sensitivity.
- [x] Run a real SQLite persistence round trip through a Unicode/spaced path.
- [x] Pass all 12 offline mandatory checks before and after local integration of the exact candidate.
- [x] Obtain a fresh independent APPROVED review bound to the exact candidate and evidence.
- [x] Obtain actual application CI results for Windows, macOS, and Linux.
- [x] Preserve the independent documentation and contract workflow.
- [x] Record an English handoff using the repository template.
- [x] Explicitly leave MVP-01 security and dependent runtime tasks unproven.

## Task and revision

- Task: MVP-02, [Issue #4](https://github.com/Lephiziel/altruforge/issues/4).
- Branch: `review/mvp-02-bootstrap`, [Draft PR #20](https://github.com/Lephiziel/altruforge/pull/20).
- Independently reviewed source commit: `65f0d894d40db5d34c48d403a1efd8e3fc430c27`.
- Source tree: `2df63d0ba0c1d1fd9dba9dc3262ae77b6efd1912`.
- Remote PR base: `0c81c5b5c0d3f5d5ce2ae50d79a91832e6bec4b4`. The branch includes predecessor `ed9d76de6135ce0ea5dad876b12af39df70fa271` and then the reviewed commit.
- This documentation update follows the source review; it does not alter the reviewed Go source, tests, or CI configuration.

## Resulting behavior

The CLI displays root help and responds to `--help` and `-h`, returns underlying help-writer errors, and rejects unsupported commands without fake success. The real SQLite test creates a database in a Unicode/spaced temporary directory, writes and reads a value, closes the database, reopens it, and checks persistence. This is not a released or fully functioning contributor harness.

## Changes

- `go.mod`, `go.sum`: Go 1.27.3; Cobra v1.10.2; `modernc.org/sqlite` v1.60.1 and pinned dependency metadata.
- `cmd/altruforge/main.go`, `internal/cli/root.go`: minimal executable and CLI.
- `internal/cli/root_test.go`, `internal/cli/sqlite_test.go`: help, error, unsupported-command and database regression tests.
- `.github/workflows/go.yml`: native application CI on Ubuntu, Windows, and macOS.
- `README.md`, `docs/development.md`, and this task handoff: documented scope and observed evidence.
- Existing documentation/contract CI remains separate; no schemas or normative contracts were changed.

## Validation

| Command or scenario | Environment | Observed result |
| --- | --- | --- |
| All 12 mandatory checks listed below | Pinned network-disabled local executor, source commit `65f0d894` | **PASS 12/12** both before and after exceptional local integration; container cleanup verified |
| Independent candidate review | Fresh external reviewer of exact candidate and mutation evidence | **APPROVED**; not recorded as Harness approval |
| Help-writer mutation experiment | Disposable isolated test | **PASS / expected FAIL / PASS** after restoring identical source |
| [Go application — branch push](https://github.com/Lephiziel/altruforge/actions/runs/44931960163) | GitHub Actions ubuntu-latest, macos-latest, windows-latest | **PASS** on all three operating systems |
| [Go application — PR](https://github.com/Lephiziel/altruforge/actions/runs/44932106464) | GitHub Actions ubuntu-latest, macos-latest, windows-latest | **PASS** on all three operating systems |
| [Documentation and draft contracts — PR](https://github.com/Lephiziel/altruforge/actions/runs/44932106438) | Separate GitHub Actions documentation job | **PASS** |
| Documentation-only follow-up commit | This PR branch revision after `65f0d894` | Check new CI runs separately before reporting their results |

The immutable candidate was checked with these 12 registered commands:

```json
[
  ["go", "mod", "download"],
  ["go", "vet", "./..."],
  ["go", "test", "./..."],
  ["go", "test", "-race", "./..."],
  ["go", "build", "-o", "/worktmp/altruforge", "./cmd/altruforge"],
  ["altruforge-gofmt-check"],
  ["markdownlint-cli2", "**/*.md"],
  ["check-jsonschema", "--check-metaschema", "spec/schemas/event.schema.json", "spec/schemas/project.schema.json", "spec/schemas/run-report.schema.json", "spec/schemas/task-lease.schema.json"],
  ["check-jsonschema", "--schemafile", "spec/schemas/project.schema.json", "examples/project.yaml", ".altruforge/project.yaml"],
  ["check-jsonschema", "--schemafile", "spec/schemas/run-report.schema.json", "examples/run-report.json"],
  ["check-jsonschema", "--schemafile", "spec/schemas/event.schema.json", "examples/event.json"],
  ["check-jsonschema", "--schemafile", "spec/schemas/task-lease.schema.json", "examples/task-lease.json"]
]
```

The original trusted check receipts, independent review, and maintenance-integration record are retained in the operator's local evidence store; they are not uploaded to this public repository. The GitHub Actions links above are separately observable public CI evidence. Go 1.27.3 is pinned in the workflow; a configured version is not a substitute for separately captured toolchain output.

## Boundaries

- The candidate was integrated into **local** `main` under one-time operator-authorized maintenance, not through an autonomous approved Harness workflow.
- No provider login, contributor task orchestration, runtime sandbox, cancellation, recovery, remote publication or release is established.
- Three-OS Go application CI validates the bootstrap jobs only, not the complete planned runtime on those hosts.
- This PR remains a Draft; upstream `main` has not changed and Issue #4 remains open.
- MVP-01 trust-boundary and supported login/isolated-execution evidence is still outstanding.

## Dependency handoff

After maintainer acceptance, the module, CLI, SQLite baseline, and cross-platform CI provide a starting point for dependent source implementation. The bootstrap does **not** satisfy or unblock any gate that requires MVP-01 execution and security evidence.

## Review notes

Unimplemented commands are deliberately rejected. No additional runtime framework, provider adapter, security exception, or schema change was introduced. SQLite uses `database/sql` and the non-CGO modernc driver; race checks enable CGO independently, and the release-style build disables it. No new ADR was required.

The evidence supports the bootstrap candidate, not a claim that the full Altruforge product or autonomous Findrail Harness flow is complete.
