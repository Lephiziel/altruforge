# MVP-02 Bootstrap the Go module and core development workflow

Status: local bootstrap source present; trusted validation and remote evidence pending.
Dependencies: None for proposing the bootstrap. MVP-01 evidence remains independent.

## Outcome

Create the actual Go development foundation without assuming that the provider/execution boundary is already proven.

## Read first

- [docs/adr/0001-reference-runtime.md](../../docs/adr/0001-reference-runtime.md)
- [docs/development.md](../../docs/development.md)
- [docs/architecture.md](../../docs/architecture.md)

## Acceptance criteria

- [ ] Initialize github.com/Lephiziel/altruforge with Go 1.27.3 and complete verified dependency checksums.
- [ ] Validate the minimal Cobra command and pinned SQLite dependency without speculative frameworks.
- [ ] Demonstrate help-output error propagation and regression sensitivity.
- [ ] Validate a real SQLite persistence round trip in a Unicode/spaced path.
- [ ] Pass all 12 mandatory local checks on the immutable candidate with trusted execution records.
- [ ] Obtain independent review of code, tests, scope, CI, and all mandatory outcomes.
- [ ] Obtain actual application CI execution URLs for Windows, macOS, and Linux.
- [ ] Preserve the independent documentation and contract workflow.
- [ ] Complete the English handoff against the repository handoff template.
- [ ] Keep MVP-01 and dependent task evidence explicitly unproven.

## Out of scope

Complete adapters, credentials, distributed services, runtime orchestration, storage migrations, and speculative abstractions.

## Handoff: changes

The supplied source implements a minimal Cobra command with explicit output writers and a thin executable entry point. Tests cover help output, underlying help writer failures, rejection of unsupported commands, and a real SQLite persistence round trip in a Unicode/spaced path. The module pins Go 1.27.3, Cobra v1.10.2, and modernc.org/sqlite v1.60.1 and supplies indirect requirements and checksums.

An independent application workflow configures formatting, dependency metadata checks, vet, tests, races, and builds on Windows, macOS, and Linux. This patch updates README and development guidance to distinguish that source implementation from planned runtime features and pending execution evidence. The documentation workflow is outside this patch.

## Handoff: validation

No tools or commands were run during this patch preparation, as required by the patch-only instruction. No mandatory check is recorded as passing. The following entries are exact argv arrays supplied by the task, not execution records:

```json
[
  ["go", "mod", "download"],
  ["go", "vet", "./..."],
  ["go", "test", "./..."],
  ["go", "test", "-race", "./..."],
  ["go", "build", "-o", "/worktmp/altruforge", "./cmd/altruforge"],
  ["altruforge-gofmt-check"],
  ["markdownlint-cli2", "**/*.md"],
  ["check-jsonschema", "--check-metaschema", "spec/schemas/event.schema.json", "spec/schemas/project.schema.json", "spec/schemas/run-report.schema.json", "spec/schemas/task-lease.schema.json"],
  ["check-jsonschema", "--schemafile", "spec/schemas/project.schema.json", "examples/project.yaml", ".altruforge/project.yaml"],
  ["check-jsonschema", "--schemafile", "spec/schemas/run-report.schema.json", "examples/run-report.json"],
  ["check-jsonschema", "--schemafile", "spec/schemas/event.schema.json", "examples/event.json"],
  ["check-jsonschema", "--schemafile", "spec/schemas/task-lease.schema.json", "examples/task-lease.json"]
]
```

The trusted workflow must record the immutable candidate identity, actual executor image digest, actual toolchain version, Linux architecture, and each command's exit status and outcome. None of those execution results was supplied. Go 1.27.3 is the configured version, not an observed toolchain result. Windows, macOS, and Linux application CI execution URLs remain absent.

The help regression mutation experiment is specified in [development guidance](../development.md). Neither its expected failure with ignored output errors nor its expected success after restoration has been observed here. Dependency checksum completeness and the SQLite round trip also remain unverified.

## Handoff: remaining work

Execute all 12 mandatory checks against the final immutable candidate through the trusted offline executor. Resolve any failures within the admitted paths and repeat checks on the resulting immutable candidate. Demonstrate the help regression test's sensitivity separately. Obtain independent review of the candidate, regression experiment, SQLite behavior, CI configuration, scope, and all mandatory results.

Compare this handoff with [the repository handoff template](../agents/HANDOFF.md) before acceptance. The template and referenced contracts were not supplied, and tools were prohibited, so template conformity and contract review cannot be established from this patch.

Obtain real application CI executions and URLs for Windows, macOS, and Linux. Configuring the workflow and passing Linux local checks cannot substitute for these executions.

## Handoff: dependencies and disposition

Issue #4 and full MVP-02 completion remain pending. Neither prior candidate 3efdb8367526c06494becc44f82f6f5ef7abba66 nor rejected candidate ed9d76de6135ce0ea5dad876b12af39df70fa271 supplies accepted completion evidence for this patch.

No dependent task becomes unblocked. MVP-01 security, supported login, execution, isolation, cancellation, and recovery remain explicitly unproven. The local bootstrap cannot certify those gates.
