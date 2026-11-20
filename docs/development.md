# Development

## Current checkout

The proposed MVP-02 bootstrap adds a minimal Cobra command and a real SQLite persistence test. Runtime execution, provider sign-in, isolation, recovery, and publication remain planned. No executable release or successful application checks are established by this proposal.

Go 1.27.3 is selected in the module and application CI. Direct dependencies are Cobra v1.10.2 and modernc.org/sqlite v1.60.1. Dependency resolution remains incomplete: the trusted offline executor must generate and verify the complete go.sum and any indirect module requirements before this candidate can pass review.

## Development commands

After dependency metadata has been completed with the trusted offline executor, use:

```sh
go mod download
go vet ./...
go test ./...
go test -race ./...
go build ./cmd/altruforge
go run ./cmd/altruforge --help
```

Check formatting with `gofmt -l cmd internal`; any output is a failure. Apply formatting with `gofmt -w cmd internal`.

The application workflow independently configures Windows, macOS, and Linux checks with Go 1.27.3. Race checks use CGO and require a supported native C toolchain. The build step disables CGO. Configuration alone supplies no execution evidence. Keep documentation and contract checks independent; their commands remain in [CONTRIBUTING.md](../CONTRIBUTING.md).

## Behavior and regression checks

The command supports root help and rejects unknown commands, including planned runtime commands. Actual output uses standard writer interfaces. Cobra's help callback cannot return an error, so Execute explicitly collects and returns help-output failures.

`TestRootHelpPropagatesWriteError` checks the underlying error identity for root help, `--help`, and `-h`. To demonstrate regression sensitivity on a disposable candidate, change Execute to return only `root.Execute()` and run `go test ./internal/cli -run '^TestRootHelpPropagatesWriteError$' -count=1`; it must fail. Restore the implementation and repeat; it must pass. This experiment has not been executed.

`TestSQLitePersistence` uses database/sql and the real modernc driver against a temporary database in a Unicode/spaced directory. It creates a table, inserts and reads a value, closes the database, reopens it, and checks persistence. Cleanup closes handles before removal of the temporary directory.

## Changes and evidence

Do not commit runtime databases, run logs, working clones, provider sessions, or credentials. Persisted runtime migrations remain outside this bootstrap.

No checks were executed while preparing this patch. Record all 12 mandatory checks, exact argv, outcomes, executor/toolchain identity, immutable candidate identity, and tested Linux architecture through the trusted workflow. Obtain independent review and actual application CI URLs for Windows, macOS, and Linux before claiming full MVP-02 completion. MVP-01 security, login, and execution evidence remains unproven; downstream gates remain blocked.
