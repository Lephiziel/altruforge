# Platform targets

## Host versus build target

Altruforge's first public MVP must run on Windows, macOS, and Linux. The initial execution profile builds and tests Linux-compatible projects. A macOS host does not imply that the Linux executor can build an Xcode-only project.

| Host target | CLI release target | Codex command sandbox route | Verification status |
| --- | --- | --- | --- |
| Windows 11 | amd64 | Codex native Windows sandbox with a least-privilege permission profile when using PowerShell; WSL2 uses the Linux sandbox. A separate Docker verifier remains a possible route. | Vendor documentation reviewed; not exercised for MVP-01. |
| macOS supported by the selected Codex release | arm64 and amd64 | Codex native Seatbelt sandbox with a least-privilege permission profile. A separate Docker verifier remains a possible route. | Vendor documentation reviewed; not exercised for MVP-01. |
| Linux | amd64 and arm64 | Codex native bubblewrap/seccomp sandbox with a least-privilege permission profile; a separate Docker verifier is possible. | Partial prototype observed on Arch Linux x86_64 only; no Ubuntu 24.04 reference-host run or end-to-end Altruforge runtime. |

Ubuntu 24.04 amd64 is the initial Linux reference environment. Other distributions and architectures require declared evidence before being described as verified. Windows arm64 is a later target unless the complete dependency chain is demonstrated.

## Compatibility policy

Minimum OS and provider versions are the intersection of the pinned Go toolchain, coding agent, executor, and authentication requirements. MVP-01 records that matrix; a generic list of OS names is not sufficient.

Resolve a container image to an immutable digest and platform before execution. Save both in the checkpoint/report. Resume cannot silently change the image. Native Codex agent sandboxing and Docker-based verification are separate boundaries; passing one does not prove the other.

## MVP-01 observed boundary status

[MVP-01 evidence](evidence/MVP-01-boundary.md) records Codex CLI `0.171.0` on Arch Linux rolling (kernel `7.3.5-arch1-1`, x86_64), with a `workspace-only` permissions profile and bubblewrap `0.13.1`. Host-home canaries and a custom environment sentinel were denied to command and child processes under that profile. Default `workspace-write` did not deny them. A temporary JSON-RPC v2 app-server probe invoked the canary, interrupted a long-running tool job, and resumed its external test checkpoint and thread from a fresh app-server process. The production Altruforge adapter/run state machine remains unimplemented. The profile is documented as beta.

The Windows PowerShell/native sandbox, Windows WSL2/Linux sandbox, and macOS Seatbelt routes above are based on [Codex sandbox documentation](https://developers.openai.com/codex/sandboxing), not execution evidence. A local Windows 11 Pro build `26200` AMD64 VM ran Codex CLI `0.171.0` with a successful ChatGPT device login. The strict `:root = deny` profile failed closed: the unelevated sandbox could not enforce split filesystem read restrictions, and the elevated sandbox helper required effective `:root` read access at `thread/start`. The profile was not weakened; no project tool, canary, cancellation, or recovery probe ran on Windows. WSL2 was not usable in this VM: VirtualBox reports nested VT-x/AMD-V disabled, and `wsl.exe --version` timed out after 15 seconds. Windows gates remain blocked. macOS evidence is waived for MVP-01 issue closure by maintainer direction recorded in ADR 0003, but macOS remains a public MVP/release-readiness requirement and is not certified by this exception. Documentation coverage or partial VM tests do not certify the OS/version matrix.

## Required platform evidence

- Installation and dependency discovery.
- Supported account login and logout.
- Paths containing spaces and non-ASCII characters.
- Non-interactive agent start, event handling, and failure.
- Termination of the entire job, not only its parent process.
- Restart and explicit resume after interruption.
- Credentials and unrelated personal files inaccessible to worker code.
- One full task-to-Draft-PR scenario on each host OS.

Cross-compilation alone does not satisfy any execution claim. Evidence is indexed in [docs/evidence](evidence/README.md).
