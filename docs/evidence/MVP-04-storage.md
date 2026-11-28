# MVP-04 durable run storage evidence

## Task and revision

- Task: MVP-04, [Issue #6](https://github.com/Lephiziel/altruforge/issues/6).
- Tested source commit: `964997e32fda05eb565ed64ddd2b2daf3f05eb0c`.
- Tested source tree: `5e020fc48ee4d3863c3700c48e2327cf4233a333`.
- Branch: `implementation/mvp-04-durable-run`.

## Environment

- Linux x86_64 (`Linux 7.3.5-arch1-1`), `linux/amd64`.
- Go `1.27.4-X:nodwarf5`, module target Go 1.27.3.
- SQLite driver: pinned `modernc.org/sqlite v1.60.1`.
- Reviewer: pending PR review.

## Scenarios and observations

| Command or scenario | Result |
| --- | --- |
| `go test ./internal/store -count=1` | PASS |
| `go test ./...` | PASS |
| `go vet ./...` | PASS |
| `go test -race ./...` | PASS |
| `CGO_ENABLED=0 go build -o /tmp/opencode/altruforge-mvp04/altruforge-test ./cmd/altruforge` | PASS; temporary binary removed |
| `git diff --check` | PASS |
| `npx --yes markdownlint-cli2 "**/*.md"` | Exit 0; CLI reported 62 files scanned and 0 lint issues |
| Child process exits after committing `preflighting`, with an uncommitted update to `awaiting_review`; parent reopens SQLite | PASS; committed state/event survive, uncommitted apparent success does not |
| Run transitions and special outcomes, effective attempt-limit enforcement, event replay/sequence, checkpoint persistence, side-effect intent/status, elapsed accumulation, sensitive fields | PASS in `internal/store` tests |
| Newer schema, incomplete versioned schema, and corrupt database open | PASS; each is rejected with an error |
| [Go application PR CI](https://github.com/Lephiziel/altruforge/actions/runs/46093847502), source commit `964997e32fda05eb565ed64ddd2b2daf3f05eb0c` | PASS on Ubuntu, macOS, and Windows (format, vet, tests, race, CGO-free build) |
| [Documentation/contracts PR CI](https://github.com/Lephiziel/altruforge/actions/runs/46093847544), same commit | PASS |

## Limitations

- Windows and macOS evidence is GitHub Actions application CI, not a local run or full product end-to-end scenario.
- No provider, workspace, CLI-orchestration, or end-to-end recovery scenario was run.
- Monotonic time between the last persisted interval and abrupt process death cannot be measured portably after restart; orchestration must conservatively enforce the remaining run budget.
- Caller payload values still require explicit secret redaction; the store rejects sensitive field names as defense in depth.

## Artifacts and review

Commands are reproducible from the tested commit. No credentials, database files, or private session artifacts are included. Independent PR review is pending.
