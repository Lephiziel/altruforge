# Development

## Current checkout

The MVP-02 source implements a minimal Cobra command and includes a real SQLite persistence test. Runtime execution, provider sign-in, isolation, recovery, and publication remain planned. Source implementation does not establish successful checks or an executable release.

Go 1.27.3 is selected in the module and application CI. Direct dependencies are Cobra v1.10.2 and modernc.org/sqlite v1.60.1. The supplied go.mod includes indirect requirements and go.sum includes dependency checksums. Their completeness and correctness remain unverified until the trusted offline executor resolves and checks the immutable candidate. Do not replace checksums with invented values.

## Development commands

With the pinned toolchain and dependencies available, use:

```sh
go mod download
go vet ./...
go test ./...
go test -race ./...
go build ./cmd/altruforge
go run ./cmd/altruforge --help
```

Check formatting with `gofmt -l cmd internal`; any output is a failure. Apply formatting with `gofmt -w cmd internal`.

The application workflow independently configures Windows, macOS, and Linux checks with Go 1.27.3. It checks committed dependency metadata, formatting, vet, tests, races, and a build without CGO. Race checks use CGO and require a supported native C toolchain. Configuration alone supplies no execution evidence. Keep documentation and contract checks independent; their commands remain in [CONTRIBUTING.md](../CONTRIBUTING.md).

## Behavior and regression checks

The command supports root help and rejects unknown commands, including planned runtime commands. Actual output uses standard writer interfaces. Cobra's help callback cannot return an error, so Execute explicitly collects and returns help-output failures.

`TestRootHelpPropagatesWriteError` checks the underlying error identity for root help, `--help`, and `-h`. Demonstrate regression sensitivity in a disposable copy by replacing `return errors.Join(root.Execute(), helpErr)` with `return root.Execute()` in Execute. Run:

```sh
go test ./internal/cli -run '^TestRootHelpPropagatesWriteError$' -count=1
```

The mutated implementation must fail because help writer errors are ignored. Restore the original implementation and repeat the same command; it must pass. Record the mutation, both outcomes, and candidate identities separately from the mandatory checks on the final immutable candidate. This experiment has not been executed during this patch preparation.

`TestSQLitePersistence` uses database/sql and the real modernc driver against a temporary database in a Unicode/spaced directory. It creates a table, inserts and reads a value, closes the database, reopens it, and checks persistence. Cleanup closes handles before removal of the temporary directory. Test source alone is not a passing round-trip result.

## Required evidence

Do not commit runtime databases, run logs, working clones, provider sessions, or credentials. Persisted runtime migrations remain outside this bootstrap.

The [MVP-02 handoff](tasks/MVP-02.md) lists the exact argv for all 12 mandatory checks. The trusted workflow must execute them on the immutable candidate and record each exit status and outcome, executor image digest, actual Go version, and tested Linux architecture. An executor image named in task configuration is not proof that it ran.

No tools or commands were run while preparing this patch, as required by the patch-only instruction. No passing checks, architecture, regression experiment, or independent review can be reported. Obtain actual application CI execution URLs for Windows, macOS, and Linux before claiming full MVP-02 completion. Issue #4 remains pending. MVP-01 security, login, and execution evidence remains unproven; downstream gates remain blocked.
