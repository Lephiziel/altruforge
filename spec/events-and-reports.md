# Events and reports

Events use newline-delimited JSON. Reports use JSON. The [event schema](schemas/event.schema.json) and [report schema](schemas/run-report.schema.json) define their draft shapes.

## Events

Each event includes `schema_version`, `run_id`, a monotonically increasing `sequence`, an RFC 3339 UTC timestamp, a type, and structured data.

Types cover state changes, task selection, public agent messages, check completion, budget notices, checkpoints, publication, and errors. Events convey user-relevant progress; they do not expose hidden reasoning.

Persist sequence allocation with state. Replaying a checkpoint must not duplicate committed event identities. Redact or omit credentials, authorization headers, session payloads, and sensitive environment values before persistence.

## Reports

A report identifies the run, outcome, repository, task when selected, immutable base/result/policy references, attempts, required checks, lease generation, and PR when created.

`usage.available: false` means measurement is unavailable. Do not infer remaining subscription allowance or fabricate token/cost values.

`awaiting_review` requires a Draft PR and successful local required checks. Upstream CI can still be pending. Other outcomes must not imply a successful handoff.

## Integrity

Artifact hashes and commit references make evidence traceable, not inherently trustworthy. A contributor controls their local machine. The project independently verifies the result and binds its status to the reviewed commit.

Schema validation alone cannot prove that a command ran, that a lease is current, or that a report came from a trusted verifier.
