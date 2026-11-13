# Altruforge specification draft 0.1

This directory defines intended interoperable behavior. It is a draft contract, not evidence of a working implementation.

**Normative** requirements use MUST, MUST NOT, SHOULD, and MAY in their ordinary specification sense. Examples illustrate the contract and do not grant execution authority.

| Contract | Definition | Machine-readable fixture |
| --- | --- | --- |
| Project | [Manifest](project-manifest.md) | [Schema](schemas/project.schema.json), [example](../examples/project.yaml) |
| Run | [Lifecycle](run-lifecycle.md) | [Report schema](schemas/run-report.schema.json), [example](../examples/run-report.json) |
| Events | [Events and reports](events-and-reports.md) | [Event schema](schemas/event.schema.json), [example](../examples/event.json) |
| Task ownership | [Coordination](coordination.md) | [Lease schema](schemas/task-lease.schema.json), [example](../examples/task-lease.json) |
| CLI | [Command and exit contract](cli.md) | Implemented and tested by MVP-13 |

## Compatibility

`schema_version` is the string `0.1`. Unknown versions and unsupported required capabilities MUST fail before work starts. Draft changes update prose, schemas, examples, and affected tasks atomically.

Objects are strict unless a schema explicitly permits extension data. A future extension mechanism needs version/capability negotiation; unknown security-relevant fields are never silently ignored.

The stable specification will define migrations before 1.0. Other implementations are welcome but MUST NOT claim compatibility based only on accepting the YAML file.

## Verification and trust

Schemas validate shape. Runtime validation also enforces cross-field semantics, path boundaries, immutable references, time/lease validity, authorization, and secret handling.

A valid JSON report is not an upstream attestation. See [verification](verification.md) and [technical references](references.md).
