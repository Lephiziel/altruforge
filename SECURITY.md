# Security policy

## Current status

Altruforge has no executable release. The draft trust model is documented in [docs/security/threat-model.md](docs/security/threat-model.md). Claims about supported isolation or platforms require the evidence defined in the MVP backlog.

## Reporting a vulnerability

Use GitHub's **Report a vulnerability** option if private vulnerability reporting is enabled for this repository. Availability is a repository setting and is not guaranteed by this file.

If that option is unavailable, open an issue titled **Request for a private security contact**. Include no exploit, credentials, affected private data, or reproduction details. The maintainer will arrange a private channel before requesting sensitive information.

There is no configured project security mailbox yet. Do not send sensitive material to guessed addresses.

## Report contents

Once a private channel exists, include the affected revision, environment, impact, reproduction steps, and any proposed mitigation. Redact account identifiers and secrets. Coordinated disclosure timing is agreed after the report is assessed.

## Runtime release requirements

A runtime release must document its provider versions, executor, platform matrix, credential boundary, and known limitations. Required isolation cannot be disabled automatically. Credentials, Docker daemon access, and publication permissions remain outside untrusted workers.

Draft PR workflows must not run untrusted pull-request code with a privileged upstream token. See [the execution decision](docs/adr/0003-execution-and-authentication.md) and [the test plan](docs/testing.md).
