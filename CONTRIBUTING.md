# Contributing to Altruforge

Altruforge is being prepared for its first MVP. The current checkout contains documentation, draft schemas, examples, and repository configuration. Runtime implementation starts with the [ordered backlog](docs/tasks/README.md).

## Choose work

Read [AGENTS.md](AGENTS.md), [START_HERE](docs/agents/START_HERE.md), and the selected task. Check existing issues and pull requests before starting. State which task you are taking and keep its scope small enough to review.

Dependencies are requirements, not suggestions. If a prerequisite has no accepted evidence, identify that gap rather than building on an assumed result.

## Local documentation checks

Install the pinned documentation tools in an isolated tooling environment, not as application dependencies:

```sh
npx --yes markdownlint-cli2@0.23.2 "**/*.md"
python -m pip install -r .github/requirements-docs.txt
check-jsonschema --check-metaschema spec/schemas/*.schema.json
check-jsonschema --schemafile spec/schemas/project.schema.json examples/project.yaml .altruforge/project.yaml
check-jsonschema --schemafile spec/schemas/run-report.schema.json examples/run-report.json
check-jsonschema --schemafile spec/schemas/event.schema.json examples/event.json
check-jsonschema --schemafile spec/schemas/task-lease.schema.json examples/task-lease.json
```

The documentation workflow runs the same checks. These commands do not test the unimplemented runtime.

Once MVP-02 introduces the Go module, follow [the development guide](docs/development.md). Keep tool versions pinned in the repository and use a supported Go release. Do not add a Go module merely to make an unrelated docs PR appear buildable.

## Pull requests

Use a branch named `docs/<topic>` or `feat/mvp-XX-<topic>`. Describe the concrete problem, resulting behavior, and validation. Link the relevant task using its MVP ID and GitHub issue when available.

Use concise commit messages such as `docs: define coordinator lease contract` or `feat: persist run checkpoints`. Conventional Commit prefixes are useful; a release automation system is not installed yet.

Every change must preserve the language policy: English only. Update affected prose, schemas, examples, and acceptance criteria together.

## AI-assisted work

AI assistance is welcome. The submitter remains responsible for understanding the change, meeting the task, preserving licensing obligations, and reporting actual verification. Describe material agent assistance in the PR template.

Never submit raw credentials, session exports, private reasoning, or copied code whose provenance and license you cannot establish. An agent's positive verdict does not replace executable checks or maintainer review.

## Architectural changes

Use [the ADR template](docs/adr/template.md) for changes to the runtime, trust boundary, coordinator, protocol, storage, or public compatibility. Routine implementation details do not require an ADR.

## Licensing and conduct

Contributions are accepted under [Apache-2.0](LICENSE). Submit work you have the right to contribute; disclose relevant third-party notices. No separate CLA is required at this stage.

Follow the [Code of Conduct](CODE_OF_CONDUCT.md). For vulnerabilities, use [SECURITY.md](SECURITY.md), not a public exploit report.
