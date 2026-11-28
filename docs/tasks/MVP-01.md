# MVP-01 Prove supported authentication and execution boundaries

Status: blocked — Linux prototype evidence recorded; Windows/macOS and runtime integration gates remain unmet.
Dependencies: None.

## Outcome

Establish a supported Codex account/execution route for Windows, macOS, and Linux before treating the boundary as a product capability.

## Read first

- [docs/adr/0003-execution-and-authentication.md](../../docs/adr/0003-execution-and-authentication.md)
- [docs/security/authentication.md](../../docs/security/authentication.md)
- [docs/security/threat-model.md](../../docs/security/threat-model.md)
- [docs/platforms.md](../../docs/platforms.md)

## Acceptance criteria

- [x] Record exact versions for the evaluated Linux environment and distinguish observations from Windows/macOS documentation review.
- [x] Demonstrate supported ChatGPT login and a non-interactive Codex CLI session on Linux without copying credentials into the sandbox.
- [ ] Demonstrate the sentinel boundary across the required host routes. Linux passed with the documented custom profile; Windows and macOS remain untested.
- [ ] Demonstrate full-runtime interruption and supervisor-owned recoverable checkpoint. A temporary Codex CLI job was interrupted/resumed, but no Altruforge checkpoint exists.
- [x] Document Windows/macOS/Linux routes and gaps; leave Windows/macOS and full-runtime gates incomplete.
- [x] Amend ADR 0003 with the Linux evidence and a supported Codex permission-profile candidate; final acceptance remains evidence-gated.

## Out of scope

A production CLI, a marketplace, additional providers, and certification based only on a green unit test.

## Required handoff

A redacted evidence record in docs/evidence/MVP-01-boundary.md, environment/version matrix, and an ADR outcome. Temporary prototypes are allowed during this future implementation task; do not pass them off as the runtime.

Use [the handoff template](../agents/HANDOFF.md). All changes and reports must be in English.

## Current handoff (2026-11-28)

See [MVP-01 boundary evidence](../evidence/MVP-01-boundary.md). Linux evidence now includes a successful supported CLI login and non-interactive turn, sentinel-denial and environment-filtering tests under a documented Codex permission profile, a bounded interruption/resume prototype, and a separate Docker isolation check. It does not establish the Altruforge app-server adapter or trusted supervisor checkpoint. Windows and macOS were unavailable. ADR 0003 remains evidence-gated; MVP-01 and dependent execution-boundary claims remain blocked.

### Task and revision

- Issue: [#3](https://github.com/Lephiziel/altruforge/issues/3).
- Branch: `research/mvp-01-boundary-evidence`.
- Evidence commit: `034258f`; the evidence scenario used Codex CLI `0.171.0` on the environment recorded in [the evidence report](../evidence/MVP-01-boundary.md). This handoff update follows that evidence commit.

### Resulting behavior and changes

This change records actual Linux provider, native sandbox, Docker, cancellation, and CLI-session-resume observations. ADR 0003 proposes the documented Codex `workspace-only` profile as the supported alternative to unrestricted host execution, but leaves acceptance gated. Platform documentation distinguishes Codex native agent sandboxing from Docker-based verification. This is research evidence, not an Altruforge runtime implementation.

### Validation

| Command or scenario | Environment | Observed result |
| --- | --- | --- |
| `codex login status` and non-interactive `codex exec --json` | Arch Linux x86_64, Codex CLI 0.171.0 | Login via ChatGPT reported; non-interactive turn returned the expected response. |
| Home-file and environment canaries under `workspace-only` profile | Arch Linux, bubblewrap 0.13.1 | Direct and child file reads denied; environment canary absent from command and child. |
| Interrupt long-running Codex command and resume session | Arch Linux, Codex CLI 0.171.0 | `timeout --signal=INT --kill-after=3 40s` returned 124; child process stopped; temporary marker persisted; `codex exec resume` succeeded. This does not validate a Harness checkpoint. |
| Restricted Docker container canaries | Docker Engine 29.10.0, Linux/amd64 | Host canaries, Docker socket, network, and writes inaccessible under the recorded limits. Not connected to Codex tools. |
| `npx --yes markdownlint-cli2 '**/*.md'` (markdownlint-cli2 0.24.2) | Linux | PASS, 61 files, zero issues. |
| Documentation workflow's pinned `check-jsonschema==0.39.0` schema/fixture commands | Python 3.13 container on Linux | PASS for all schemas and project, report, event, and lease fixtures. |

### Boundaries and dependency handoff

Acceptance criteria for the live provider session and Linux-native sandbox are partially met. The actual app-server protocol, app-server/tool execution integration, supervisor-owned checkpoint, and complete Windows/macOS scenarios remain unverified. Keep MVP-01 and all dependent execution-boundary work blocked until those exact gates have evidence. See the evidence report for the proposed next test matrix and limitations.

### Review notes

The candidate was amended based on observed failure of default `workspace-write` and observed success of the documented `workspace-only` profile on Linux. The profile is beta; no platform portability or production integration claim is made. No credentials or raw canary contents are committed.
