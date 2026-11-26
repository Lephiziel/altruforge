# Candidate publication: initial formal specification

This is a finite-state abstraction of the pre-completion publication protocol. It is a research model, not a runtime design or implementation proof. The executable model is `CandidatePublication.tla`; TLC configurations distinguish the full safety relation from liveness under a recovery environment that does not crash again.

## System state and trust boundaries

The system has one orchestrator and one forge. The orchestrator holds a durable publication intent and phase. The forge holds a feature ref, a pull request identity, and a verification status identity. `remoteHead`, `remotePR*`, and `remoteStatus*` represent forge state; recovery predicates use these variables, not local completion claims. `observed` records that a remote read was made before the terminal decision.

The model treats the orchestrator's durable ledger as crash-persistent and the forge's accepted effects as persistent. A process crash loses volatile control and acknowledgement but does not erase either durable intent or accepted forge effects. The model's `Crash` transition represents that loss by moving the phase to `unknown` without changing persistent fields.

Trust boundary: candidate bytes and verification identity are inputs from a prior trusted verification step. The model does not prove the verifier, agent, forge implementation, API response authenticity, TLS, host, credentials, or storage implementation trustworthy. Forge observations are assumed to report current state accurately in the base model.

## Immutable identities and effect identity

The model instantiates one task and one repository; these are fixed by the model instance rather than represented as changing variables. Within that scope, a run is represented by the unique constant `RunId`. Its candidate is `CandidateSha`, based on immutable `BaseSha`, and its verification receipt is `VerificationDigest`. `PersistIntent` durably records the run key and all three evidence identities before any modeled external effect. No later transition changes the recorded intent tuple.

The modeled PR identity is the tuple `(fixed repository identity, RunId, BaseSha, CandidateSha)`. The repository is fixed by this model instance rather than a changing variable. The modeled status identity is `(CandidateSha, VerificationDigest)`. A status for another commit or verification receipt cannot satisfy the completion predicate. The feature ref is the candidate SHA. This abstraction contains one task, one repository, and one PR identity slot; it does not represent arbitrary PR multiplicity, cross-repository collision, or full provider payloads.

## States and transitions

`phase` is one of `idle`, `intent`, `recovering`, `complete`, `conflict`, or `unknown`.

- `idle -> intent`: persist the run, base, candidate, and verification identity.
- `intent/recovering -> recovering`: update the feature ref only when its current value is the expected base; create the exact PR only when the modeled PR slot is empty; write the status only for the exact candidate and verification identity. Each external effect is a separate transition, so interruption can occur between effects.
- `intent/recovering -> unknown`: crash. Persistent intent and all already accepted forge effects remain unchanged; the acknowledgement is not modeled as durable.
- `unknown -> recovering`: resume from persisted intent.
- `recovering/unknown -> complete`: only after a remote read sees the candidate ref, exact PR tuple, and exact status tuple.
- `recovering/unknown -> conflict`: remote read sees a competing ref value.
- `recovering/unknown -> recovering`: remote read sees incomplete effects, allowing reconciliation to continue.
- `intent/recovering -> recovering`: a concurrent writer may move the ref from base to `DriftSha`. `DispatchRef` then cannot overwrite it because its guard requires `BaseSha`.

Terminal `complete` and `conflict` are absorbing in this abstraction. Permanent provider read failures, API result ambiguity, permission changes, deletion, external mutation after terminal completion, and multiple concurrent runs are not transitions in this initial model.

## Crash and recovery semantics

The durable intent precedes dispatch. An effect may be accepted by the forge while the orchestrator still records only an in-progress phase. After restart, the orchestrator must re-read remote state and reconcile every required effect by identity. A timeout or lost acknowledgement is not evidence that an effect did not occur. An unreadable or incomplete state must not be reported as complete.

`Crash` is included in the safety model at every in-progress phase and can occur repeatedly. The conditional liveness model deliberately omits further `Crash` transitions: it tests eventual progress only after interruptions cease. This is not a claim that arbitrary repeated interruption permits liveness.

## Safety properties

TLC checks these invariants for every reachable state under `Spec`:

1. `TypeOK`: phase, intent, ref, PR, and status identities stay within the finite domains.
2. `IntentIdentityStable`: every non-idle phase has exactly the original run, candidate, base, and verification identity.
3. `CompleteHasExactEvidence`: `complete` implies the exact intent, candidate ref, matching PR, matching candidate-bound status, and a completed remote observation.
4. `RemoteEffectIdentitiesStayBound`: any recorded PR or status effect has the intended immutable identities.

The transition guard on `DispatchRef` preserves a competing ref by allowing the candidate update only from the expected base. The state abstraction does not model arbitrary external writers after a terminal decision, so this property should not be generalized beyond the modeled interval.

## Conditional liveness

`EventuallyTerminal` states that an in-progress, recovering, or unknown intent eventually reaches `complete` or `conflict`. TLC checks it only under `FairRecoverySpec`, which assumes: provider reads and writes represented by enabled recovery actions eventually run (weak fairness); the durable intent remains available; the provider remains readable/writable; and no further crash occurs during recovery. A permanent ref conflict may reach `conflict`; successful `complete` is not promised in that case.

This is a bounded finite model with one run and one candidate, not a proof for all values, implementations, or executions.

## Provider assumptions and impossibility boundaries

The model assumes a single compare-and-swap-like ref update from the expected base, stable immutable commit IDs, a queryable exact PR identity, candidate-scoped status, durable accepted forge effects, and accurate current reads. The P0.1 Forgejo observations establish only selected version-specific behaviors for Forgejo 17.0.2.

If a request times out and the provider cannot be read, the client cannot distinguish “effect absent” from “effect applied but acknowledgement lost” from client-side evidence alone. Safe progress then requires waiting, a provider-supported idempotency key, a reliable read/query by immutable identity, or a human decision. No retry protocol can manufacture exactly-once effects where the provider exposes neither idempotent creation nor authoritative reconciliation. A stale or eventually consistent read may also make `complete` unsound unless the provider contract supplies a suitable consistency guarantee.

The model excludes observation failures and stale reads; the supplementary protocol is preregistered to exercise those boundaries. No universal exactly-once, statistical superiority, equivalence, novelty, or production correctness claim follows from this model or the pilot.
