# Research questions

The unit of analysis is one logical publication intent for a verified immutable artifact. The questions are conditional on explicitly profiled provider capabilities; no provider is assumed to supply a global transaction.

## RQ1 — Late settlement

Can a delayed remote effect invalidate a recovery decision made while the effect is unresolved? Compare settlement before recovery, after a successful absence observation, and after recovery dispatch; inspect whether terminal classification or duplicate effects become unsound.

## RQ2 — Concurrent publishers

Under what endpoint guarantees (atomic compare-and-swap, server-enforced fencing, deduplication key, serialization, or none) can multiple publishers preserve the specified publication safety properties? Identify minimal sufficient combinations within the bounded model and tested endpoint profiles.

## RQ3 — Artifact identity

Under what conditions does the publication remain bound to the exact verified candidate when branch/ref names are mutable? Trace the verifier's content digest and commit identity through intent, request, provider state, and observer evidence.

## RQ4 — Observation consistency

Which observation guarantees are necessary for sound `complete`, `not_executed`, and `conflict` classifications? Compare linearizable, monotonic/versioned, bounded-stale, inconsistent, unavailable, and timeout responses. `unknown` remains an allowed correct classification when evidence is insufficient.

## RQ5 — Repeated recovery failures

Can arbitrary finite recovery crashes preserve safety while allowing eventual terminal progress after crashes cease, remote effects settle, observations recover, and enabled steps receive fair scheduling? Separately characterize executions where one of these assumptions never holds.

RQ1-RQ5 are distinct. RQ1/RQ2/RQ4 concern endpoint timing and observations; RQ3 concerns identity binding; RQ5 concerns temporal progress under fairness. RQ2/RQ4 may be answered by conditional counterexamples rather than a single provider-independent rule.
