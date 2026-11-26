# Reproducibility

## Current state

NIR-04 primary trials have not run. The documentation and model are in a separate worktree/branch from NIR-03. At preparation time, `/usr/bin/java` is OpenJDK `27.0.1.1`; `tlc`, `tlatex`, and a local `tla2tools` JAR were not found in PATH or the searched local project/tool directories. The NIR-03 checkout contains its own TLC v1.8.0 output and recorded commands, but that does not make the NIR-04 extension checked. Outbound GitHub access was unavailable during PR closeout checks. No model-checking result is claimed for this extension. Tool discovery is preserved in [`formal/runs/TOOL-AVAILABILITY.md`](formal/runs/TOOL-AVAILABILITY.md).

## TLC reproduction when tooling is provisioned

Use `tla2tools.jar` from the [official TLA+ tools releases](https://github.com/tlaplus/tlaplus/releases); the project documents command-line use and Java 11+ requirement. Pin an immutable release/build and verify its SHA-256 against a trusted publisher-provided value before use. Record URL, version, Java version, SHA-256, exact command, host/runtime and raw stdout/stderr. From repository root:

```sh
java -cp /path/to/verified/tla2tools.jar tlc2.TLC \
  -config research/nir-04/formal/StrongEndpoint.cfg \
  research/nir-04/formal/PublicationRecovery.tla
java -cp /path/to/verified/tla2tools.jar tlc2.TLC \
  -config research/nir-04/formal/WeakObservation.cfg \
  research/nir-04/formal/PublicationRecovery.tla
java -cp /path/to/verified/tla2tools.jar tlc2.TLC \
  -config research/nir-04/formal/NoFreshness.cfg \
  research/nir-04/formal/PublicationRecovery.tla
java -cp /path/to/verified/tla2tools.jar tlc2.TLC \
  -config research/nir-04/formal/UnsafeAbsence.cfg \
  research/nir-04/formal/PublicationRecovery.tla
java -cp /path/to/verified/tla2tools.jar tlc2.TLC \
  -config research/nir-04/formal/InconsistentObservation.cfg \
  research/nir-04/formal/PublicationRecovery.tla
java -cp /path/to/verified/tla2tools.jar tlc2.TLC \
  -config research/nir-04/formal/UnavailableObservation.cfg \
  research/nir-04/formal/PublicationRecovery.tla
java -cp /path/to/verified/tla2tools.jar tlc2.TLC \
  -config research/nir-04/formal/NoCAS.cfg \
  research/nir-04/formal/PublicationRecovery.tla
java -cp /path/to/verified/tla2tools.jar tlc2.TLC \
  -config research/nir-04/formal/NoFence.cfg \
  research/nir-04/formal/PublicationRecovery.tla
java -cp /path/to/verified/tla2tools.jar tlc2.TLC \
  -config research/nir-04/formal/RetryOnlyDedup.cfg \
  research/nir-04/formal/PublicationRecovery.tla
java -cp /path/to/verified/tla2tools.jar tlc2.TLC \
  -config research/nir-04/formal/RetryOnlyNoDedup.cfg \
  research/nir-04/formal/PublicationRecovery.tla
java -cp /path/to/verified/tla2tools.jar tlc2.TLC \
  -config research/nir-04/formal/MutableArtifact.cfg \
  research/nir-04/formal/PublicationRecovery.tla
java -cp /path/to/verified/tla2tools.jar tlc2.TLC \
  -config research/nir-04/formal/ConditionalLiveness.cfg \
  research/nir-04/formal/PublicationRecovery.tla
```

Write raw logs and any TLC state traces under `research/nir-04/formal/runs/<tool-version>/<profile>/`. Preserve counterexamples unchanged. Before interpreting, run TLC parser/type checking, review the model against this specification, validate each configuration, and report state counts and any error. The weak profile is intended to expose counterexamples, not to be silently fixed until it passes. A profile passing TLC is finite bounded evidence only.

## Future primary experiment (not authorized)

No setup or execution command is issued here. Before a separate approval and preregistration, a fresh checkout must pin a provider image by digest, verify binary/image provenance, build disposable local fixtures, apply the frozen seed/assignment file, run an infrastructure-only smoke test in separate repositories, and prove the observer is read-only. Secret material is injected at runtime from a local secret store and must not appear in shell history, captures, or public artifacts. The exact container/image digest, fixture commands, runner/evaluator commit, environment allowlist, random seed, and output locations must be recorded in the future protocol.

Archive raw evidence privately with manifest SHA-256, per-file digests and access procedure. Public outputs must be scanned for tokens, cookies, private URLs, personal data and private repository names; record redactions without publishing secrets. Failed smoke checks and post-start infrastructure failures are retained separately and never replaced. These safeguards address the NIR-03 intermediate-ledger, HTTP-404, aggregate-event and evidence-retention limitations prospectively; they do not revise NIR-03.
