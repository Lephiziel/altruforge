# Independent review record

## Review scope and independence

A separate read-only reviewer inspected the NIR-04 draft after initial assembly and again after the first corrections. The reviewer did not edit the branch or observe any primary trial data; no primary trials exist. Findings below are preserved as received in substance. A final read-only review of the current revision is pending before this branch is presented as ready for owner review.

## First review — findings

The review considered literature relevance, gap framing, model soundness, baseline fairness, hypothesis alignment, statistical assumptions, and reproducibility. It found the literature appropriately cautious, but rejected preregistration readiness due to model and design gaps:

- No explicit `not_executed` state or retry requests, leaving delayed-effect-after-absence and deduplication comparisons unmodeled.
- Fencing could reject an old request after recovery while one-shot dispatch prevented recovery from retrying, undermining stated liveness.
- Freshness was recorded but not required by completion classification; review/status observations lacked a distinct inconsistency abstraction.
- Ref integrity was not tied to its originating request and receipt.
- H1 did not match the confirmatory policy estimand; multiplicity and power assumptions required clarification.
- The independent oracle needed a frozen journal/snapshot schema and reconciliation smoke check; per-arm decision limits needed explicit rules.

## Corrections made after first review

- Added bounded retries (two requests per operation per publisher), `not_executed`, safe-absence and freshness profile switches, and stale/inconsistent model configurations.
- Bound ref integrity to a settled ref request, publisher, artifact, and receipt; strengthened `not_executed` soundness to require authoritative actual absence and no pending request.
- Remapped H1 to the sole confirmatory retry-only versus contract-aware contrast under delayed settlement; marked settlement timing as secondary.
- Marked 650 paired blocks as provisional planning under a 0.20 discordance scenario rather than a conservative bound; required simulation across 0.10/0.20/0.30 discordance and plausible missingness before preregistration.
- Specified per-arm stopping/decision rules, separated treatment observation budgets from oracle/evaluator reads, and required a schema-frozen smoke reconciliation proving journal/snapshot consistency and no fixture-semantic perturbation.
- Excluded malformed/mismatched verifier behavior from the current study unless separately specified and validated.

## Second review — remaining findings

The reviewer re-read the first corrected draft and found the same core model blockers still present in that revision: one request per operation, no `not_executed`, a fencing/liveness dead end, freshness not enforced, and insufficient ref provenance binding. The reviewer also reiterated H1/estimand mismatch and the need to treat 0.20 discordance as an assumption, not an upper bound. The corrections above were made after receiving this second review; therefore it is not represented as approval of the current version.

## Third review — findings and current response

The final review judged the proposal ready for owner design review, but not preregistration or trials. It found remaining issues: unbounded epochs contradicted finite-state scope; liveness allowed dispatch after `not_executed` and only required eventual one-time terminal reachability; `SoundNotExecuted` consulted mutable global state rather than decision-time evidence; capability profiles were confounded; per-endpoint observation staleness was incomplete; logical deduplication needed a direct invariant; and the fixed stale/unavailable schedule allocation was not specified.

Subsequent edits replace publisher-local saturating epochs with a shared provider-side highest-accepted fence token and a bounded unique token sequence (no token reuse), prevent redispatch after terminal `not_executed`, snapshot decision-time remote evidence, add unconditional logical uniqueness, isolate capability/freshness/absence profiles, and fix the primary target mix at 50/50 stale/unavailable. The model now requires at least one dispatch before `not_executed` and states both eventual-terminal and eventual-stable-terminal properties for dispatched intents. Review/status endpoints still do not have independently stale versions. These updates were reviewed in a final read-only pass. The decision evidence snapshots cover actual ref/review/status/pending state at classification, but the remote observation abstraction still applies staleness only to ref; this limitation is disclosed. The model remains unvalidated formal design material.

## Current review status

The final reviewer identified three post-review defects: a 0..4 epoch type bound against token 5 assignment, duplicate `RequireFresh` assignments in `NoFreshness.cfg`, and the retry model forbidding resend while an earlier request remained pending. The current working revision widens the epoch type, removes the duplicate constant, and allows only the `RetryOnly` profile to resend while a same-operation effect remains pending. The reviewer rechecked these corrections and found no remaining must-fix static transition inconsistency.

**Final verdict:** suitable for owner design review as a candid, non-authorizing proposal; not formal validation, preregistration evidence, or authorization to run primary trials. The reviewer did not run TLC or trials. Remaining limits include bounded token/retry domains and incomplete per-endpoint stale-read modeling (review/status currently sample actual state). These boundaries remain documented rather than treated as established guarantees.
