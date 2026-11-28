# MVP-01 Prove supported authentication and execution boundaries

Status: blocked — Linux prototype evidence recorded; Windows strict sandbox did not initialize. macOS execution evidence is waived for this issue by maintainer direction, but remains required for public release readiness.
Dependencies: None.

## Outcome

Establish supported Codex account/execution evidence for Windows and Linux before treating the boundary as a product capability. Native macOS evidence is waived for this issue only by the maintainer; public release readiness still requires it.

## Read first

- [docs/adr/0003-execution-and-authentication.md](../../docs/adr/0003-execution-and-authentication.md)
- [docs/security/authentication.md](../../docs/security/authentication.md)
- [docs/security/threat-model.md](../../docs/security/threat-model.md)
- [docs/platforms.md](../../docs/platforms.md)

## Acceptance criteria

- [x] Record exact versions for the evaluated Linux environment and distinguish observations from Windows/macOS documentation review.
- [x] Demonstrate supported ChatGPT login and non-interactive Codex CLI/app-server sessions on Linux without copying credentials into the sandbox.
- [ ] Demonstrate the sentinel boundary on Linux and Windows. Linux passed with the documented custom profile. Windows ChatGPT login and app-server startup were attempted, but the strict profile failed closed before project tools ran (unelevated filesystem restriction failure; elevated helper requires effective `:root` read access). WSL2 was unavailable in the VM (nested virtualization disabled; `wsl.exe --version` timed out). macOS execution evidence is waived for this issue only; see ADR 0003. This does not certify macOS for product release.
- [x] Demonstrate full-job interruption and recoverable checkpoint in a temporary Linux app-server supervisor prototype; a fresh app-server resumed the stored thread. This is not the Altruforge production run state machine.
- [x] Document Windows/macOS/Linux routes and gaps, the maintainer-directed macOS issue waiver, and the remaining Windows/product release-readiness gates.
- [x] Amend ADR 0003 with the Linux evidence and a supported Codex permission-profile candidate; final acceptance remains evidence-gated.

## Out of scope

A production CLI, a marketplace, additional providers, and certification based only on a green unit test.

## Required handoff

A redacted evidence record in docs/evidence/MVP-01-boundary.md, environment/version matrix, and an ADR outcome. Temporary prototypes are allowed during this future implementation task; do not pass them off as the runtime.

Use [the handoff template](../agents/HANDOFF.md). All changes and reports must be in English.

## Current handoff (2026-11-28)

See [MVP-01 boundary evidence](../evidence/MVP-01-boundary.md). Linux evidence includes a successful supported login, non-interactive CLI and app-server v2 turns, sentinel-denial and environment-filtering tests under a documented Codex permission profile, and a temporary app-server supervisor prototype that persisted a checkpoint before work, interrupted the full tool job, stopped its child, and resumed the thread/checkpoint from a fresh server process. Windows ChatGPT login succeeded and the app-server was invoked on Windows 11 Pro build 26200/AMD64 using a prepared Unicode/spaced path, but the strict root-read-denial profile failed closed before project tools ran; Windows canary, cancellation, and recovery are not evidenced. WSL2 could not be used in this VM because nested virtualization is disabled and `wsl.exe --version` timed out. Per maintainer direction, macOS evidence is waived for this issue only, not for public release readiness. MVP-01 remains blocked on Windows evidence; ADR 0003 remains evidence-gated.

### Task and revision

- Issue: [#3](https://github.com/Lephiziel/altruforge/issues/3).
- Branch: `research/mvp-01-boundary-evidence`.
- Evidence commit: `33365a6`; the evidence scenario used Codex CLI `0.171.0` on the environment recorded in [the evidence report](../evidence/MVP-01-boundary.md). This handoff update follows that evidence commit.

### Resulting behavior and changes

This change records actual Linux provider, app-server v2, native sandbox, Docker, cancellation, and checkpoint/session-recovery observations. ADR 0003 proposes the documented Codex `workspace-only` profile as the supported alternative to unrestricted host execution, but leaves cross-platform acceptance gated. Platform documentation distinguishes Codex native agent sandboxing from Docker-based verification. This is research evidence, not an Altruforge runtime implementation.

### Validation

| Command or scenario | Environment | Observed result |
| --- | --- | --- |
| `codex login status` and non-interactive `codex exec --json` | Arch Linux x86_64, Codex CLI 0.171.0 | Login via ChatGPT reported; non-interactive turn returned the expected response. |
| Home-file and environment canaries under `workspace-only` profile | Arch Linux, bubblewrap 0.13.1 | Direct and child file reads denied; environment canary absent from command and child. |
| Temporary app-server JSON-RPC v2 handshake, turn, and sandboxed canary call | Arch Linux, Codex CLI 0.171.0 | PASS; profile denied canaries and filtered environment marker. No Altruforge adapter was involved. |
| Temporary app-server cancellation and fresh-process recovery | Arch Linux, Codex CLI 0.171.0, JSON-RPC v2, Python 3.14.10 | PASS; outside-workspace checkpoint persisted before work, `turn/interrupt` stopped the child, and fresh app-server `thread/resume` restored the conversation/checkpoint. Probe scripts require Python 3.10+. Not an Altruforge runtime. |
| Independent Codex CLI process-group interruption | Arch Linux, Codex CLI 0.171.0 | `SIGINT` stopped the observed child host process; temporary marker persisted; `codex exec resume` succeeded. |
| Restricted Docker container canaries | Docker Engine 29.10.0, Linux/amd64 | Host canaries, Docker socket, network, and writes inaccessible under the recorded limits. Not connected to Codex tools. |
| Windows ChatGPT login and app-server strict-profile attempt | Windows 11 Pro build 26200/AMD64, Codex CLI 0.171.0, Python 3.14.10 | Login passed. Unelevated sandbox refused the `:root = deny` profile; after elevated setup in the dedicated `CODEX_HOME`, app-server `thread/start` failed because the helper requires effective `:root` read access. No project tool ran; permission profile was not weakened. |
| Windows WSL2 route availability | Windows 11 Pro VM in VirtualBox 7.2.22 | WSL executable and registry key were present, but `wsl.exe --version` timed out after 15 seconds; VirtualBox reports nested VT-x/AMD-V disabled. No WSL distribution or sandbox test was run. |
| `npx --yes markdownlint-cli2 '**/*.md'` (markdownlint-cli2 0.24.2) | Linux | PASS, 61 files, zero issues. |
| Documentation workflow's pinned `check-jsonschema==0.39.0` schema/fixture commands | Python 3.13 container on Linux | PASS for all schemas and project, report, event, and lease fixtures. |

### Boundaries and dependency handoff

Acceptance criteria for the live provider session, Linux-native sandbox, and Linux interruption/checkpoint prototype are met for the tested host only. Windows provider login is evidenced, but the required strict boundary is not: both Windows sandbox paths stopped before project tools, and no canary, cancellation, or recovery result was obtained. macOS evidence is waived for issue closure by maintainer direction, but remains an explicit release-readiness requirement. Keep MVP-01 and dependent execution-boundary work blocked until Windows evidence is obtained. See the evidence report and ADR 0003 for limitations and the scope exception.

### Review notes

The candidate was amended based on observed failure of default `workspace-write` and observed success of the documented `workspace-only` profile on Linux. The profile is beta; no platform portability or production integration claim is made. No credentials or raw canary contents are committed.
