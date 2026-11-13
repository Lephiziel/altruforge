# MVP-05 Implement GitHub identity and isolated Git workspaces

Status: not implemented.
Dependencies: [MVP-02](MVP-02.md)

## Outcome

Connect the contributor identity and prepare pinned public-repository workspaces and forks.

## Read first

- [docs/security/authentication.md](../../docs/security/authentication.md)
- [docs/architecture.md](../../docs/architecture.md)
- [spec/cli.md](../../spec/cli.md)

## Acceptance criteria

- [ ] Use a supported GitHub login route; a supervised GitHub CLI auth adapter is an acceptable MVP choice and must declare that dependency.
- [ ] Verify the active account without printing tokens or storing them in the worktree/report; document connection ownership and logout behavior.
- [ ] Read only public targets in the MVP and require project opt-in before creating contribution work.
- [ ] Clone/fetch with explicit argument arrays, pin the trusted base, and handle spaces/non-ASCII paths safely.
- [ ] Prepare a contributor-owned fork/branch without requiring upstream collaborator access.
- [ ] Classify revoked auth, missing access, network failure, and an existing fork without destructive retries.

## Out of scope

Custom browser-session extraction, organization-wide access changes, and private-repository support.

## Required handoff

Redacted auth/workspace tests, GitHub fixture evidence, and a documented dependency/account flow.

Use [the handoff template](../agents/HANDOFF.md). All changes and reports must be in English.
