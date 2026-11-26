# Hypotheses and falsification plan

These hypotheses are scoped to the protocol profiles and schedules specified in the future experiment. Formal counterexamples test model claims; randomized trials estimate empirical event rates. No general “exactly once” outcome is the target.

## H1 — Late settlement and recovery policy (RQ1; sole confirmatory contrast)

**Null:** in the preregistered weak-endpoint population with accepted-but-unacknowledged delayed creates, retry-only and contract-aware reconciliation differ by less than the prespecified 5 percentage-point meaningful margin in unsound terminal classifications. **Alternative:** the absolute paired risk difference is at least 5 points in either direction. **IV:** assigned policy (retry-only versus contract-aware); settlement-after-ambiguous-response is held as a required schedule stratum. **DV/estimand:** paired risk difference in unsound terminal classifications. **Observable:** independent-oracle score at the fixed horizon, plus late effects after that horizon. **Falsification:** a sufficiently precise interval excludes effects of 5 points or larger; this does not establish equivalence. **Confounds:** provider queueing, schedule fidelity, observation lag, policy budget. **Scope/significance:** one fixture contract and declared schedule population.

The settlement-before-read versus settlement-after-absence timing contrast is secondary and exploratory, not a second confirmatory hypothesis. It is estimated only if both strata pass oracle-integrity checks and reported with the designated secondary-family multiplicity correction.

## H2 — Concurrent publishers (RQ2)

**Null:** within the tested two-publisher schedule set, endpoint capability profile does not change the rate of unauthorized ref/object mutation by 5 percentage points or more. **Alternative:** at least one tested profile differs by at least 5 points, or TLC finds a safety counterexample for a profile. **IV:** CAS, server-side deduplication, server-enforced fencing, and publisher interleaving. **DV/estimand:** rate of unauthorized/divergent mutation per assignment and duplicate objects per intent. **Falsification:** no bounded counterexample and powered interval excludes a 5-point profile effect. **Confounds:** provider implementation/version, operation ordering, key scope. **Scope/significance:** conditional capabilities; not a provider ranking.

## H3 — Artifact identity (RQ3)

**Null:** mutable-ref-only and digest/commit-bound profiles have an identity-mismatch risk difference below 5 percentage points under concurrent ref mutation. **Alternative:** the mutable-ref-only profile has at least a 5-point increase, or a bounded trace substitutes a candidate without detection. **IV:** immutable identity binding and concurrent ref mutation. **DV/estimand:** per-assignment published digest mismatch and detection rate. **Falsification:** powered interval excludes a 5-point increase and bounded model finds no undetected substitution in the mutable-only profile. **Confounds:** Git object availability, merge/rebase behavior, hash parsing. **Scope/significance:** examines traceability, not cryptographic hash collision resistance.

## H4 — Observation consistency (RQ4)

**Null:** stale/inconsistent versus fresh coherent reads change false `complete`/`not_executed` classification risk by less than 5 percentage points. **Alternative:** weaker reads cause at least a 5-point increase or TLC exhibits one unsound terminal trace. **IV:** read consistency and cross-endpoint version coherence. **DV/estimand:** unsound classification risk and time to a sound classification. **Falsification:** powered interval excludes the threshold and no bounded counterexample exists for the weaker profile. **Confounds:** hidden caches, pagination, index lag. **Scope/significance:** identifies observation requirements by classification.

## H5 — Repeated recovery failures (RQ5)

**Null:** for every finite crash schedule in the bounded model, if crashes cease, remote requests eventually settle/reject, fresh observations remain available, and recovery/provider actions are weakly fair, all intents eventually reach complete or conflict while invariants hold. **Alternative:** there exists a trace satisfying every stated premise that violates an invariant or never reaches a terminal phase. **IV:** crash positions/count and premises toggled. **DV:** invariant violation and terminal-eventuality. **Falsification:** a TLC counterexample under all premises falsifies the bounded null; a pass only supports the bounded model. **Confounds:** finite-state bounds, fairness strength, effect/observation abstraction. **Scope/significance:** distinguishes safety under repeated finite crashes from progress after stable recovery.

For H1-H4, a null result is not evidence of equivalence. Trial-level null interpretation requires confidence intervals against predeclared meaningful margins and sufficient power. Hypotheses can be rejected as trivial/untestable after independent review; no treatment selection will be changed after observing outcomes.
