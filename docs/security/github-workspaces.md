# GitHub identity and workspaces (MVP-05)

## Dependency and account flow

MVP-05 requires the supported [GitHub CLI (`gh`)](https://cli.github.com/) installed and available on `PATH`. Authenticate through GitHub CLI's supported device/browser flow, for example `gh auth login --hostname github.com --web --git-protocol https`; follow the CLI prompt to complete sign-in. Altruforge reuses the active `gh` account and verifies it with `gh auth status` and `gh api user`. It reports the account login only. It does not read, copy, print, persist, or mount the token or the `gh` credential store.

The GitHub session is owned by the contributor/GitHub CLI, not Altruforge. `gh auth logout --hostname github.com` is an explicit user action; Altruforge logout must not delete the shared CLI session. Missing `gh` is a dependency failure; revoked authentication, missing access, network failure, and existing forks are distinct outcomes. The adapter redacts process output and never retries account, fork, or Git operations destructively.

GitHub access is limited by behavior to public repositories. A selected repository must have a valid `.altruforge/project.yaml` in its trusted default-branch base with `enabled: true` and a matching `project.repository`. Altruforge checks this before fork creation or contribution branch setup. Private targets are rejected. Fork creation is performed through `gh repo fork` under the contributor's account; upstream collaborator access is not requested. Existing contributor forks are reused and reported, never overwritten.

The workspace is cloned with explicit argument arrays, resolves and records the default branch's immutable Git commit, and creates a local branch at exactly that commit. The contributor fork is added as a separate remote. Repository paths are handled as filesystem arguments (including spaces and Unicode); no shell command strings are used. GitHub CLI credentials remain in the CLI's existing OS-managed credential store and Git may use the user's configured credential helper when later pushing; neither is copied into the workspace.

## Logout and scope

Removing a local project selection or workspace does not affect the contributor's global GitHub CLI session or upstream repository. To disconnect, the contributor uses the GitHub CLI's own logout command. Organization-wide changes, custom browser-session extraction, and private repositories are unsupported.

## Evidence

Deterministic adapter and local-Git fixture tests cover account verification without token output, public/private target handling, opt-in, pinned base, safe Unicode/spaced paths, branch/fork remotes, and rejection of existing workspace paths. Live account verification and GitHub Actions results are recorded in the MVP-05 task handoff; tests do not create a fork in an unsuspecting repository.
