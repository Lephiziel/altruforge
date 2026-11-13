# MVP scope

## Required end-to-end result

A contributor on Windows, macOS, or Linux can connect GitHub and the first supported coding agent, choose an opted-in GitHub project, and start a bounded run. The tool selects one eligible issue, obtains a valid task lease, announces its plan, implements and checks a patch, and creates at most one Draft PR for that run.

The contributor receives the PR link, local verification results, upstream CI status if known, and any limitations. The run ends after handoff. The maintainer decides what to merge.

## First supported surface

- GitHub public repositories and contributor-owned forks.
- Codex as the first completely tested agent adapter.
- Local contributor execution with an explicit execution boundary.
- Linux-compatible build/test projects, hosted from all three required operating systems.
- YAML project configuration, schema validation, JSON reports, and JSONL events.
- Persistent checkpoints, explicit resume, cancellation, time limits, retry limits, and bounded concurrent work.
- Project-controlled coordination and independent upstream checking.

Source discovery starts with GitHub Issues. File-based backlogs can be a later TaskSource adapter. The implementation backlog in `docs/tasks/` is for developing Altruforge itself.

## Defaults and limits

A contributor runs one task at a time by default. The project limits open harness PRs and active leases. A run defaults to 30 minutes and at most two implementation attempts unless a stricter project or contributor limit applies.

Required permissions or capabilities cannot be weakened automatically. Missing credentials, unavailable isolation, incompatible versions, unresolved acceptance criteria, and quota exhaustion produce explicit outcomes.

A paused run does not resume when a quota resets unless the contributor requests it. Usage is reported only when the provider makes it available; the tool does not promise a precise percentage of remaining subscription allowance.

## Excluded from the first public MVP

A global marketplace, GUI, multi-provider parity, native Xcode/Windows build environments, autonomous roadmap ownership, automatic merging, and unattended replies to maintainer feedback.

## Acceptance

Every requirement in [release readiness](../release-readiness.md) needs recorded evidence. The first public release requires a complete scenario on Windows, macOS, and Linux; a successful cross-build is insufficient.

The public README must distinguish specification, implemented behavior, and verified platforms. No planned installer, package, integration, or test result may be presented as available.
