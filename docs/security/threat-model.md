# Trust model

## Assets and authority

Protect contributor accounts, personal files, paid usage, upstream repositories, task ownership, and verification evidence.

The contributor authorizes a bounded run. The maintainer authorizes task eligibility and project policy. The runtime enforces these constraints. Issue content, repository scripts, model output, and an outside contributor's report are untrusted inputs.

## Boundaries

| Boundary | Requirement |
| --- | --- |
| Project configuration | Load from a pinned trusted base; hash the effective policy |
| Worker execution | Restrict filesystem, network, environment, resources, and lifecycle |
| Credentials | Keep outside worker-readable storage and inherited environment |
| Task ownership | Accept only coordinator-authorized, current lease generations |
| Verification | Required checks cannot be replaced by agent assertions or PR-controlled policy |
| Publication | Validate lease, policy, result commit, and idempotency before handing off |
| Upstream CI | Never execute untrusted PR code with a privileged upstream write token |

## Cases that must be tested

Prompt injection in an issue; a project script reading home/auth directories; a child surviving cancellation; a leaked environment token; a forged local report; simultaneous claims; expired or revoked leases; lost publication responses; and changes to verification configuration inside a proposed patch.

## Executor decision

A Docker container alone is not a demonstrated guarantee. The host supervisor retains daemon access; workers do not receive its socket or host home. OS-native agent isolation and container-based verification must be evaluated as a complete system.

No automatic fallback to unrestricted host execution is allowed. If a required capability is unavailable, report blocked.

The accepted execution boundary and its limitations require evidence under [ADR 0003](../adr/0003-execution-and-authentication.md). Kernel-level attacks and native-platform build support need explicit treatment before making broader security claims.

## Reporting

Follow [SECURITY.md](../../SECURITY.md). Public evidence is redacted. Do not include raw session exports or hidden model reasoning in logs or PRs.
