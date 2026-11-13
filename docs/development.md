# Development

## Current checkout

There is no Go module or runtime implementation yet. The repository currently checks documentation and draft data contracts. Follow [CONTRIBUTING.md](../CONTRIBUTING.md) for the working documentation commands.

MVP-02 owns Go module initialization, pinned dependencies, the build command, and actual Go CI. Do not invent a passing runtime build before that task lands.

## Runtime toolchain decision

Use a supported stable Go toolchain and pin the selected version in the Go module and CI together. Cobra is the CLI library; SQLite is accessed through `database/sql` and `modernc.org/sqlite` so release builds need not depend on CGO.

Provider and executor integrations remain adapters. Avoid an orchestration framework, service mesh, broker, or external database until a measured requirement justifies one.

## Checks introduced with implementation

Once the Go module exists, MVP-02 must establish and document:

```sh
go fmt ./...
go vet ./...
go test ./...
go test -race ./...
go build ./cmd/altruforge
```

Use a race-enabled CI environment with its required toolchain. A CGO-free release configuration does not imply that the race detector works in that same configuration.

Add contract, integration, and cross-platform tests as their tasks land. A normal test run must not spend a contributor's real subscription or create upstream PRs.

## Changes and state

Do not commit runtime databases, run logs, working clones, provider sessions, or credentials. Use temporary directories in tests. Persisted data migrations need forward compatibility checks and recovery behavior.

A task handoff must state the exact commands run, their outcomes, tested OS/architectures, and missing live-provider evidence.
