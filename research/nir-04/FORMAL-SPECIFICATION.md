# Formal specification extension

## Boundary and trust

The model extends NIR-03 from one publisher to a finite set of two publishers. Each publisher has a durable intent with a run identifier, immutable artifact digest, Git commit, base ref, and verification receipt bound to that digest. The remote service has a mutable branch ref, a set of created logical review objects, and a request queue whose effects may settle after local timeout or recovery. Acknowledgement may be lost or delayed. Publisher-local observations may be stale, inconsistent across endpoints, unavailable, or fresh. Crashes erase volatile state but preserve durable intent and provider state.

Trusted in the model: collision resistance and correct digest computation, correct verifier receipt semantics, durable local intent once acknowledged by local storage, and provider behavior exactly as selected by a capability profile. Not trusted: network delivery timing, response arrival, or that absence of acknowledgement means absence of effect. The model does not represent malicious provider behavior, compromised credentials, Git hash collisions, full Git merge semantics, real HTTP parsing, or arbitrary Byzantine faults.

## Identity and effects

An artifact identity is `(digest, commit)`; a branch/ref is a mutable locator only. A verification identity is `(receipt, digest, verifier policy)`. Publication intent binds publisher/run, expected base, artifact identity, verification identity, target repository, and idempotency key (if provider supports it). A remote effect identity is `(provider, repository, operation, key)` for deduplicated endpoints; absent server-side deduplication, each request may create an independent effect. Acknowledgement is a local observation of a response, not the effect identity.

## State transitions

1. `PersistIntent`: durable immutable intent before any remote dispatch.
2. `Dispatch`: enqueue a request; remote effect may remain pending while the publisher times out or crashes.
3. `Settle`: provider applies or rejects pending request, honoring configured CAS, fence, and dedup contracts.
4. `Acknowledge`: response is delivered or lost independently of settlement.
5. `Crash` / `Recover`: volatile state is cleared; recovery reads durable intent and resumes observation/reconciliation.
6. `Observe`: endpoint returns current, stale, inconsistent, unavailable, or error evidence.
7. `Classify`: complete only on evidence meeting the configured contract; otherwise conflict, not-executed, or unknown.

## Properties

- **Artifact integrity:** every accepted remote publication points to the digest bound by the corresponding verification receipt.
- **Authorization:** every mutation has a durable intent authorized for that repository and operation; expired publisher epochs cannot mutate when server-enforced fencing is part of the profile.
- **Sound completion:** a `complete` classification implies remote ref/object/status identities match the durable intent at a valid observation linearization point. With no fresh/linearizable point, classification remains unknown.
- **Uniqueness (conditional):** at most one logical object per intent only where provider-side idempotency/deduplication is atomic. Otherwise retries may create duplicates; the model reports this boundary rather than asserting uniqueness.
- **Recovery safety:** crashes preserve durable intent and cannot authorize a different artifact or verification receipt.
- **Conditional liveness:** if crashes cease after finite time, pending effects settle or reject within finite time, observations eventually become available and meet their stated consistency profile, conflicts stop, and enabled recovery/provider actions are fairly scheduled. Dispatch fairness is policy-shaped: contract-aware dispatch waits for a fresh observation and an unsatisfied operation; retry-only dispatch ignores observations and may resend while an earlier effect remains pending (the bounded dispatch action abstracts timeout expiry; no timeout clock is modeled). Then a dispatched intent eventually reaches a sound terminal classification (`complete`, `conflict`, or `not_executed`); the latter is a valid terminal result when the provider rejects all effects. The model also checks that terminal classification is eventually stable after dispatch. If an assumption fails indefinitely, terminal progress is not required.

## Impossibility boundaries and open refinements

If a request can remain delayed forever while observations cannot distinguish “not applied” from “applied but invisible,” a client cannot soundly choose both to retry and to assert no effect. Similarly, a client-side lease without provider-enforced fencing cannot prevent a delayed former holder from mutating state. These are model-level indistinguishability arguments, not claims that every forge behaves this way. A provider's concrete CAS, deduplication, visibility, and timeout contract must be verified separately.

The initial TLA+ extension models two publishers, up to two requests per operation per publisher (12 request identifiers total), explicit `not_executed` classification, endpoint-scoped idempotency keys, pending settlement independent of acknowledgement, receipt-to-digest binding, repeated crashes, and fresh/stale/inconsistent/unavailable read profiles. Terminal soundness is evaluated against a per-publisher decision-time snapshot so later concurrent changes do not retroactively invalidate an earlier observation. Review/status reads currently sample actual state; stale and inconsistent behavior is applied to the ref endpoint, so independent staleness of all three endpoints remains unmodeled. Ref, review and status operations settle independently. `SafeAbsence` and `RequireFresh` expose weak classifier profiles for counterexample checks; strong profiles require no unresolved request and fresh evidence. Separate configurations vary CAS, fencing, deduplication, and digest binding one at a time, while stale/inconsistent/unavailable profiles are explicitly named. Ref provenance is tied to the settled request, publisher, artifact and receipt. The retry bound is two requests per operation, request identifiers are finite, a global provider fence clock starts after two distinct initial tokens and assigns ordered tokens through 5, allowing at most four recovery advances; further recovery is disabled at the finite token bound. Settlement ticks are capped by the 12-request bound. A provider-side highest-accepted token rejects delayed requests with smaller tokens once a higher token has been accepted. The finite model cannot make claims beyond four recovery-token advances. This makes the state space finite; behavior after the recovery bound is out of scope. The two-artifact domain is an explicit abstraction; it does not model arbitrary retry counts, verifier compromise or invalid attestations, full Git object/merge behavior, provider schema evolution, status updates after creation, or multiple repositories. The model-checking artifact is finite and bounded. TLC evidence, if available, is not a mathematical proof of the implementation or of unbounded executions.
