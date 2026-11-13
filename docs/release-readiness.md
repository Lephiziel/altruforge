# First public MVP release gate

A release is a maintainer decision supported by evidence. None of the runtime requirements below is currently marked complete.

## Required evidence

- [ ] MVP-01 records a supported authentication/execution route and provider version matrix.
- [ ] Required Go, contract, and integration checks pass.
- [ ] A full task-to-Draft-PR scenario passes on Windows, macOS, and Linux.
- [ ] Cancellation terminates the full job; crash/restart does not duplicate publication.
- [ ] Concurrent claims and stale lease generations cannot both publish as authorized work.
- [ ] Required checks are controlled outside agent self-assessment.
- [ ] Worker code cannot read contributor credentials or unrelated personal files.
- [ ] Quota, auth, and unavailable-isolation failures stop clearly; no silent API billing fallback exists.
- [ ] Several bounded contributions have received maintainer review, including records of failed attempts.
- [ ] Supported versions, known limitations, install instructions, and recovery steps are documented.
- [ ] Release binaries have checksums, source revision references, and actual packaging tests.
- [ ] A usable private security/contact process is configured before soliciting sensitive reports.

## Release contents

Publish only actual build artifacts. Do not register a package, publish an installer, or advertise a download that has not been built and tested. Documentation must state the verified host and build-target matrix.

MVP-14 owns packaging and release automation. The bootstrap setup does not contain a release workflow or a pretend application build.

## Evidence format

Use [the evidence index](evidence/README.md). Each record includes revision, OS/architecture, dependency versions, command or scenario, observed result, artifacts, limitations, and reviewer. Redact all credentials and account/session secrets.
