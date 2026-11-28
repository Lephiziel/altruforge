# MVP-05 Implement GitHub identity and isolated Git workspaces

Status: implemented in [PR](https://github.com/Lephiziel/altruforge/pull/REPLACE); awaiting maintainer review and merge. Implementation tests pass on Linux; native Windows/macOS evidence is pending CI.
Dependencies: [MVP-02](MVP-02.md)

## Outcome

Connect the contributor identity and prepare pinned public-repository workspaces and forks.

## Read first

- [docs/security/authentication.md](../../docs/security/authentication.md)
- [docs/architecture.md](../../docs/architecture.md)
- [spec/cli.md](../../spec/cli.md)

## Acceptance criteria

- [x] Use GitHub CLI's supported browser/device login flow; declare `gh` as a required dependency.
- [x] Verify the active account without printing tokens or storing them in the worktree/report; document connection ownership and logout behavior.
- [x] Read only public targets in the MVP and require trusted-base project opt-in before fork/branch setup.
- [x] Clone and inspect with explicit argument arrays, pin the trusted base, and handle spaces/non-ASCII paths safely.
- [x] Prepare a contributor-owned fork/branch without upstream collaborator access.
- [x] Classify revoked auth, missing access, network failure, and existing forks without destructive retries.

## Out of scope

Custom browser-session extraction, organization-wide access changes, and private-repository support.

## Handoff

### Task and revision

- Task: MVP-05, [Issue #7](https://github.com/Lephiziel/altruforge/issues/7).
- Branch: `feat/mvp-05-github-workspaces`.
- PR: pending link replacement after publication.

### Resulting behavior

`internal/forge/github` verifies the active `gh` account, reads only public repositories, and prepares or reuses contributor-owned forks. It classifies auth, access, network, dependency, and existing-fork failures without echoing command output. `internal/workspace` checks the trusted default-branch opt-in, clones with argv, resolves and checks out the exact base commit, and creates a separate contribution branch and contributor remote. Workspace setup never asks for upstream write access.

### Changes

- Added GitHub CLI and workspace adapters with injectable command runners.
- Added redacted auth/failure and real local-Git fixture tests (including Unicode/spaced workspace path).
- Added pinned `gopkg.in/yaml.v3` for parsing the repository opt-in manifest.
- Documented dependency, sign-in, account ownership, logout and workspace behavior in [GitHub workspace security](../security/github-workspaces.md).

### Validation

| Command or scenario | Environment | Observed result |
| --- | --- | --- |
| `go test ./internal/forge/github ./internal/workspace` | Linux, Go 1.27.4, local fixtures | PASS |
| `gh auth status --hostname github.com` and `gh api user --jq .login` | Contributor's existing GitHub CLI session | PASS; only account identity checked, no token output |
| Live public repository metadata read | GitHub API, public Altruforge repository | PASS; no fork or write operation performed |
| Windows/macOS application CI | GitHub Actions | Pending PR workflow; not claimed here |

### Boundaries

This adapter does not take ownership of or implement removal of the user's global `gh` session. No live fork was created; fork creation and existing-fork behavior are fixture-covered. Full project-manifest validation remains the responsibility of the manifest task/runtime; this adapter enforces the enabled flag, repository identity, duplicate-key rejection and trusted-base location. Native Windows/macOS execution remains pending CI, and MVP-01's separate credential/execution isolation gate remains unproven.

### Dependency handoff

MVP-08, MVP-09, MVP-12 and MVP-13 can consume the public identity/workspace adapter after this PR is accepted. MVP-08 still requires MVP-03; MVP-09 additionally requires MVP-03 and MVP-08; MVP-12 also requires MVP-08, MVP-10 and MVP-11; MVP-13 also requires MVP-03, MVP-04, MVP-06, MVP-10 and MVP-12. This work does not satisfy MVP-01 or authorize runtime publication.

### Review notes

Existing user-owned forks are reused and surfaced in the result. The implementation never pushes, changes upstream permissions, removes a user's global credentials, or places credentials in a workspace.

Use [the handoff template](../agents/HANDOFF.md). All changes and reports must be in English.
