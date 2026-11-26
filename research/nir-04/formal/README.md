# Formal model and configurations

`PublicationRecovery.tla` is a finite abstraction with two publishers, two candidate artifacts, twelve request identifiers (maximum two attempts per operation and publisher), and a shared provider fence clock with unique tokens for the initial publishers and up to four subsequent recovery advances. The finite token and retry/resource bounds are abstraction choices, not production limits.

Configurations are deliberately separated:

- `StrongEndpoint.cfg`: fresh evidence, digest binding, CAS, fencing, deduplication, safe absence, freshness-required contract-aware dispatch; checks safety plus liveness. `RetryOnlyDedup.cfg` and `RetryOnlyNoDedup.cfg` compare blind bounded retries with only deduplication changed. `RetryOnly` resends while an earlier same-operation request may still be pending, without trusting an observation; contract-aware dispatch requires a fresh observation showing the operation remains unsatisfied. Both are bounded to two requests per operation. No separate timeout clock is modeled: the retry action represents a timeout firing while the remote effect remains unresolved.
- `WeakObservation.cfg`: stale ref observations with safe absence/freshness enforcement retained.
- `NoFreshness.cfg`: stale ref observations while freshness enforcement is disabled; intended to expose unsound terminal classification.
- `UnsafeAbsence.cfg`: fresh reads but no pending-request guard for `not_executed`; intended to expose the late-effect/absence race.
- `InconsistentObservation.cfg`: inconsistent ref read with conservative freshness enforcement.
- `UnavailableObservation.cfg`: observations unavailable; unknown must remain possible and liveness is not claimed.
- `NoCAS.cfg`, `NoFence.cfg`, and `MutableArtifact.cfg` each weaken one endpoint capability at a time. `RetryOnlyDedup.cfg` versus `RetryOnlyNoDedup.cfg` checks unconditional logical uniqueness under the retry-only policy.
- `ConditionalLiveness.cfg`: strong profile with fair observation, settlement, dispatch, eventual stable availability, and eventual stable publisher uptime.

Recovery increments one shared token clock; the provider stores the highest accepted token and rejects later settlement from lower tokens. Initial tokens are distinct for the two publishers. This is a bounded idealized provider contract; it does not model lease acquisition or provider deployment mechanics. These descriptions state intended checks only. No configuration has been run with TLC in this environment. No pass, state count, or counterexample is claimed. See [`runs/TOOL-AVAILABILITY.md`](runs/TOOL-AVAILABILITY.md) and the exact command list in [`../REPRODUCIBILITY.md`](../REPRODUCIBILITY.md).
