# NIR-03 retrospective

This interpretation preserves every NIR-03 classification and does not re-score any run. Source records: [`research/nir-03/FINAL_REPORT.md`](../nir-03/FINAL_REPORT.md), [`FINAL_REVIEW.md`](../nir-03/FINAL_REVIEW.md), and the original/replication result artifacts.

## What the evidence demonstrated

- P0.1 retained its 25 assigned trials. Eligible classifications showed 4/4 resolution in each of the contract-aware and candidate-reconciliation strategies; no resolution advantage was observed.
- Original supplementary S1 assigned 14 cells, all blocked by a fixture configuration defect before treatment execution. Those are infrastructure failures, not outcome data.
- S1-R2 executed the 14 fixed scenario-policy assignments after a separately documented correction and smoke check. Independent capture-based evaluation reported 10 complete, 2 not_executed, and 2 conflict; the two policies had matching terminal classifications in this small run.
- The finite NIR-03 TLA+ model was checked with TLC v1.8.0: safety model, 26 distinct states; conditional-liveness model, 16 distinct states; no error in those configured runs. Failed initial checks and traces remain preserved.
- R4 proxy evidence shows one upstream POST/201 per cell with dropped acknowledgement; aggregate barrier arrays duplicated that same event. Observer captures show one PR/status per cell.

## Unsupported properties

NIR-03 does not establish statistical equivalence, superiority, broad generality, production readiness, or a universal exactly-once property. It does not establish behavior under multiple competing publishers, delayed settlement after a recovery decision, stale-but-successful reads, mutation after terminal classification, or a permanent observation outage. Its one-instance Forgejo experiment cannot characterize other providers.

## Why no advantage was demonstrated

The preregistered S1-R2 set had one trial per scenario-policy cell, only seven scenarios, a single Forgejo version and a small descriptive outcome set. The policies shared classifications in the observed assignments. This design has little ability to estimate rare safety violations or detect modest differences. P0.1's eligible result counts also matched. Matching observed labels are not an equivalence test and cannot support equivalence absent a margin, a powered design, and a suitable interval/test.

## Assumptions that constrain interpretation

The observer was a separate process with a distinct read-only credential, but driver, observer and proxy shared the Forgejo instance and host. Provider correctness and response freshness were assumed. The initial finite model trusted the local durable ledger and exact observations and excluded concurrent runs and stale reads. The S1-R2 evaluator's 404-plus-empty-list edge case could label an unobserved branch state not_executed; observed R1 cells included later successful HTTP 200 base-SHA reads, so this defect did not change those reported labels. Intermediate `unknown` ledger writes were not retained as separate file-level snapshots. The original records themselves remain unchanged.

## Discriminating scenarios and prior answers

Scenarios likely to distinguish approaches include: a create accepted remotely but acknowledged after a recovery worker has classified absence; two publishers racing to update one ref with divergent immutable commits; old successful reads arriving after a newer write; an old lock holder's delayed request after lease expiry; repeated crash after each durable-state transition; and verifier receipt/head mismatch under a mutable branch. Existing RPC, saga, consensus, idempotence, controller-reconciliation, linearizability, and fencing work already answers parts of the general problem. NIR-04 must isolate the publication-specific interaction among these known mechanisms rather than present retries, intents, or reconciliation as novel.
