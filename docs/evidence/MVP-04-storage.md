# MVP-04 durable run storage evidence

## Task and revision

- Task: MVP-04, [Issue #6](https://github.com/Lephiziel/altruforge/issues/6).
- Tested source commit: `b59a8420aeaf4f632c58fcccc1ffdfba64999550`.
- Tested source tree: `faed9dc52ace1794a8b400ec5d211df119eb2e79`.
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
| `npx --yes markdownlint-cli2 "**/*.md"` | Exit 0; CLI reported 61 files scanned and 0 lint issues |
| Child process exits after committing `preflighting`, with an uncommitted update to `awaiting_review`; parent reopens SQLite | PASS; committed state/event survive, uncommitted apparent success does not |
| Run transitions and special outcomes, attempts, event replay/sequence, checkpoint persistence, side-effect intent/status, elapsed accumulation, sensitive fields | PASS in `internal/store` tests |
| Newer schema, incomplete versioned schema, and corrupt database open | PASS; each is rejected with an error |
| [Go application PR CI](https://github.com/Lephiziel/altruforge/actions/runs/46092986364), PR head `79e12d53031557f6d89ffb9d87f4e82b1ac919ef` | PASS on Ubuntu, macOS, and Windows (format, vet, tests, race, CGO-free build) |
| [Documentation/contracts PR CI](https://github.com/Lephiziel/altruforge/actions/runs/46092986305), same PR head | PASS |

## Limitations

- Windows and macOS evidence is GitHub Actions application CI, not a local run or full product end-to-end scenario.
- No provider, workspace, CLI-orchestration, or end-to-end recovery scenario was run.
- Monotonic time between the last persisted interval and abrupt process death cannot be measured portably after restart; orchestration must conservatively enforce the remaining run budget.
- Caller payload values still require explicit secret redaction; the store rejects sensitive field names as defense in depth.

## Artifacts and review

Commands are reproducible from the tested commit. No credentials, database files, or private session artifacts are included. Independent PR review is pending.
