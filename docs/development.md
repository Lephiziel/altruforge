# Development

## Current checkout

[Draft PR #20](https://github.com/Lephiziel/altruforge/pull/20) contains the MVP-02 Go bootstrap: minimal Cobra help/error handling and a real SQLite persistence test. No executable release is published. Provider sign-in, contributor task execution, isolation, cancellation, recovery and publication remain unimplemented or unverified.

The independently reviewed source commit is `65f0d894d40db5d34c48d403a1efd8e3fc430c27` with tree `2df63d0ba0c1d1fd9dba9dc3262ae77b6efd1912`. It passed 12/12 mandatory isolated offline checks before and after exceptional operator-maintenance local integration, and received fresh independent external APPROVED review. This is not an autonomous Harness approval or remote merge.

The module and application CI select Go 1.27.3, Cobra v1.10.2, and `modernc.org/sqlite` v1.60.1. The three-OS GitHub Actions matrix checks dependency metadata, formatting, vet, tests, race tests, and a build with CGO disabled.

## Development commands

With Go 1.27.3 and dependencies available, run from repository root:

```sh
go mod download
go vet ./...
go test ./...
go test -race ./...
go build ./cmd/altruforge
go run ./cmd/altruforge --help
```

Race checks require a native C toolchain with `CGO_ENABLED=1`. A CGO-free release-style build can use:

```sh
CGO_ENABLED=0 go build ./cmd/altruforge
```

Check formatting with `gofmt -l cmd internal`: output means failure. Apply formatting with `gofmt -w cmd internal`.

## Behavior and regression checks

The command supports root help, `--help`, and `-h`. Unsupported commands are rejected. Because Cobra's help callback cannot return an error, `Execute` joins the underlying help-output error with the command execution error.

`TestRootHelpPropagatesWriteError` checks the underlying writer-error identity on all supported help paths. In a disposable regression experiment, the normal test passed, changing `return errors.Join(root.Execute(), helpErr)` to `return root.Execute()` failed as expected, and restoring byte-identical source passed again. The targeted command is:

```sh
go test ./internal/cli -run '^TestRootHelpPropagatesWriteError$' -count=1
```

`TestSQLitePersistence` exercises `database/sql` and the real `modernc.org/sqlite` driver in a temporary Unicode/spaced directory, checking data before and after closing and reopening the database. Both test files are covered by passing native Go CI on three operating systems.

## Observed verification

- [Go application push run 44931960163](https://github.com/Lephiziel/altruforge/actions/runs/44931960163): **PASS** on Ubuntu, Windows and macOS for source SHA `65f0d894`.
- [Go application PR run 44932106464](https://github.com/Lephiziel/altruforge/actions/runs/44932106464): **PASS** on Ubuntu, Windows and macOS for the same SHA.
- [Documentation/contracts PR run 44932106438](https://github.com/Lephiziel/altruforge/actions/runs/44932106438): **PASS** in the separate documentation workflow for the same SHA.
- Pinned offline executor: **12/12 mandatory checks PASS** before and after the local maintenance integration. The receipts remain in the operator's local evidence store and are not part of the public GitHub CI logs.
- Independent external reviewer: **APPROVED** for the exact candidate and evidence, not an approved Harness review transition.
- A subsequent documentation-only commit must pass its own GitHub Actions checks before that revision can be marked passing.

The exact required offline commands and handoff are in [MVP-02](tasks/MVP-02.md). Keep the documentation and draft-contract workflow independent from application CI; see [CONTRIBUTING.md](../CONTRIBUTING.md).

## Scope and limitations

Do not commit runtime databases, workspace clones, run logs, credentials or provider sessions. Migrations of future persisted runtime state need forward-compatibility and recovery checks. A working CLI bootstrap is not evidence that provider sign-in, real sandbox boundaries, process-tree termination, or remote publication works.

PR #20 remains a Draft and [Issue #4](https://github.com/Lephiziel/altruforge/issues/4) remains open until maintainer acceptance. MVP-01 evidence is separate and outstanding; dependent gates remain blocked.
