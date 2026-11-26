# NIR-03 assignment completion audit

This audit covers the P0.1 assignment and the completion/scientific-artifact requirements requested in PR #29 follow-up. Evidence paths are relative to this directory unless stated. The 25-cell P0.1 results are preserved without edits.

| Requirement | Evidence | Status and boundary |
| --- | --- | --- |
| Formal system state and trust boundaries | `formal/SPECIFICATION.md` | Documented, including trusted verifier inputs, durable local intent, provider state, and excluded infrastructure failures. |
| Immutable candidate and verification identity | `formal/SPECIFICATION.md`, `formal/CandidatePublication.tla` | Run, base, candidate SHA, and verification digest are persisted before effects and fixed in the model. |
| Publication intent and remote effect identity | `formal/SPECIFICATION.md` | Intent and exact PR/status identities specified; model has one run and one PR slot. |
| State transitions | `formal/SPECIFICATION.md`, `formal/CandidatePublication.tla` | Prepare, individual effects, drift, crash, resume, observation, completion, conflict, and incomplete recovery modeled. |
| Crash/recovery semantics | Same artifacts | Safety relation permits repeated crashes without loss of durable intent/effects; liveness check assumes crashes cease. |
| Safety invariants | `formal/Safety.cfg`, `formal/runs/v1.8.0/safety.log` | TLC v1.8.0 checked TypeOK, stable intent, exact completion evidence, and effect identity binding across 26 reachable states. |
| Conditional liveness | `formal/ConditionalLiveness.cfg`, `formal/runs/v1.8.0/conditional-liveness.log` | TLC checked eventual terminal classification across 16 distinct states under weak fairness and no further crash transitions. This is not arbitrary-crash liveness. |
| Raw model-checking output and counterexamples | `formal/runs/` | Final pass logs and exact failed-model snapshots/configs/traces are retained. The initial liveness counterexample demonstrates that unbounded repeated crashes defeat the liveness property. |
| Provider assumptions and impossibility boundaries | `formal/SPECIFICATION.md` | Accurate/readable provider, CAS-like ref operation, stable identities, durable intent/effects, and no exactly-once inference under unreadable ambiguous requests are explicit. |
| Supplementary preregistration | `supplementary/PREREGISTRATION.md`, `supplementary/fixture-recipe.md` | Separate S1 prereg covers 14 assignments, three recovery crashes, explicit candidate-ledger `unknown`, unavailable reads for ref/PR/status, ambiguous applied effects, and remote drift. S1 is not executed. |
| Oracle independence audit | `ORACLE_AUDIT.md` | P0.1 fields come from direct Forgejo API GET responses, not orchestrator completion claims. The observer process shares the driver and credential, so it is not independently captured; S1 requires a separate observer. |
| Fresh-checkout reproducibility | `REPRODUCIBILITY.md`, `prepare_forgejo.sh` | Exact Forgejo version/signature/fingerprint, loopback config, scoped token, run/evaluation commands and cleanup are documented. Setup helper and API token were smoke-tested from a fresh `/tmp` root; token was revoked and removed. |
| Preserve original P0.1 matrix | `pilot-results.json`, `pilot-results-contract-discovery.json` | Both files remain byte-for-byte equal to commit `047f2ae765591c5098f9396d7d8591b0955f2a79`; original protocol and result files are not combined with S1. |
| Update PR #29; do not merge | PR #29 | This commit is intended for PR #29. The PR remains open; no merge or auto-merge was invoked. |
| Scientific and product limitations | `README.md`, `evaluation.md`, `formal/SPECIFICATION.md` | One run per cell, one Forgejo version, no stale-read test in P0.1, draft PR unsupported, finite model abstraction, no production implementation, and no statistical superiority/equivalence/novelty/exactly-once claim are disclosed. |

## Final disposition

The original P0.1 exploratory Forgejo pilot has been completed, scored by a separate evaluator from recorded provider-read observations, and preserved. The formal initial model has been executed by TLC with bounded results and retained counterexamples. P0.1's provider-backed oracle is not independently captured; that limitation is stated rather than concealed, and the supplementary protocol requires an independent observer before outcome collection. The new S1 protocol is preregistered and remains pending execution. No production reconciliation, MVP acceptance change, production Harness access, merge, or automatic merge has occurred.
