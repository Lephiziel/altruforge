# Platform targets

## Host versus build target

Altruforge's first public MVP must run on Windows, macOS, and Linux. The initial execution profile builds and tests Linux-compatible projects. A macOS host does not imply that the Linux executor can build an Xcode-only project.

| Host target | CLI release target | Initial execution route | Verification status |
| --- | --- | --- | --- |
| Windows 11 | amd64 | Compatible Linux execution environment, such as Docker Desktop | Not yet tested |
| macOS supported by the selected executor | arm64 and amd64 | Compatible Docker Engine through a desktop/VM environment | Not yet tested |
| Linux | amd64 and arm64 | Compatible Docker Engine | Not yet tested |

Ubuntu 24.04 amd64 is the initial Linux reference environment. Other distributions and architectures require declared evidence before being described as verified. Windows arm64 is a later target unless the complete dependency chain is demonstrated.

## Compatibility policy

Minimum OS and provider versions are the intersection of the pinned Go toolchain, coding agent, executor, and authentication requirements. MVP-01 records that matrix; a generic list of OS names is not sufficient.

Resolve a container image to an immutable digest and platform before execution. Save both in the checkpoint/report. Resume cannot silently change the image.

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
