# NIR-03 final research report

## Research question

Under repeated recovery interruptions, ambiguous forge effects, unavailable observations, and competing ref updates, can recovery distinguish unexecuted work from applied-but-unacknowledged effects and conflict while preserving immutable candidate and verification identities? The study examines specific synthetic workflows on Forgejo 17.0.2; it does not test a production implementation.

## Method

NIR-03 has three separate evidence sets. P0.1 is the preserved 25-trial matrix comparing a contract-aware baseline with candidate reconciliation. Its original evaluator found no resolution advantage in eligible cases (4/4 versus 4/4). The original supplementary S1 experiment assigned 14 cells, but all 14 were blocked during fixture setup by a malformed Git environment (`GIT_CONFIG_COUNT=2` with only one key/value pair). Those blocked records remain unchanged and are not treated as experimental outcomes.

S1-R2 corrected the Git environment with an allowlisted child environment, added Git configuration regression tests, and passed an infrastructure-only smoke suite before outcome collection. The preregistered amendment retained S1’s question, scenarios, policies, assignment count, and evaluation rules. One fresh disposable Forgejo 17.0.2 instance, separate read-only observer process/credential, and unique repository per assignment were used. Seven scenarios were run once under each of two policies. Faults included HTTP 503 reads, a forwarded create whose acknowledgement was dropped, three synchronized recovery-worker kills, and competing ref drift. A frozen evaluator recomputed terminal results from observer captures rather than driver completion labels.

The protocol, exact commands, environment setup, observer scopes, raw evidence archive, and reproducibility instructions are in [`supplementary/s1-r2/EXECUTION-AND-AUDIT.md`](supplementary/s1-r2/EXECUTION-AND-AUDIT.md), [`REPRODUCIBILITY.md`](REPRODUCIBILITY.md), and [`supplementary/s1-r2/archive/ARCHIVE-README.md`](supplementary/s1-r2/archive/ARCHIVE-README.md). Failed infrastructure-only smoke iterations v1–v5 and passing iterations v6–v8 are preserved in a separate archive; none enters the experimental denominator. The NIR-03 experimental program is frozen; these documents do not authorize rerunning an assignment.

## Formal model

The TLA+ model represents one orchestrator, one forge, one run, one candidate, one PR slot, and one verification receipt. Durable intent is fixed before effects; remote ref/PR/status effects persist across modeled crashes; recovery re-reads exact identities; a competing ref produces conflict; completion requires exact evidence. TLC v1.8.0 checked the safety model over 26 distinct states and the conditional-liveness model over 16 states with no error. Failed initial checks and counterexamples are preserved.

This is a bounded abstraction, not a proof of an implementation. It trusts the verified candidate and verification input, durable local storage, provider effects, and accurate current observations. It excludes stale reads, permanent observation failures, multiple runs/repositories, provider compromise, and mutations after terminal completion. Liveness assumes weak fairness and that crashes stop.

## Findings

Independent S1-R2 evaluation found **10 `complete`, 2 `not_executed`, and 2 `conflict`** across 14 assignments, with no missing or unexpected assignments and no capture errors. Both policies had the same terminal classifications in this run. R1 resolved to `not_executed` after restored reads showed the base ref and no PR/status. R6 resolved to `conflict` after restored reads showed the competing SHA. R2, R3, R4, R5, and R7 ended `complete` with one exact PR and status each. All prescribed outage responses were captured. R5 reached all three synchronization barriers under both policies, with each worker kill confirmed. In R4, each underlying proxy log shows one upstream HTTP 201 create and dropped acknowledgement; the aggregate barrier array duplicates that same event three times per row. The original records are preserved, and the discrepancy is audited in [`r4-barrier-audit.json`](supplementary/s1-r2/r4-barrier-audit.json).

The smoke and replication are infrastructure and exploratory evidence, respectively. The original S1 blocked assignments provide no scientific outcomes. No positive or negative policy advantage can be inferred from 14 descriptive cells, and matching labels do not establish equivalence.

## Limitations and threats to validity

- One Forgejo version, one host, one instance, one trial per scenario-policy cell, and synthetic repository operations limit external validity.
- Driver, observer, and proxy share the same host and Forgejo instance. The observer uses a distinct process and read-only credential, but provider correctness and API freshness remain assumptions.
- The runner records intermediate `unknown` driver classifications and writes an `unknown` candidate ledger after failed reads, but the ledger file is later overwritten with terminal classification. Only terminal ledger snapshots were preserved, so there is no independent file-level checkpoint proving each intermediate durable write.
- The frozen evaluator permits branch HTTP 404 alongside empty PR/status lists as `not_executed`. A missing branch is not proof that it remains at base. Recorded R1 classifications are based on later successful HTTP 200 reads of the base SHA, so this edge case does not change these outcomes. The evaluator and scoring output were preserved unchanged.
- The R4 aggregate barrier entries contain duplicated log records; underlying proxy events and observer state show one create per cell. This is a measurement/reporting defect, not evidence of repeated remote effects.
- The original S1 setup failure and bounded model counterexamples are preserved, but early infrastructure-only smoke debugging attempts are not part of the experimental denominator.

## Implications for future research

Future work should snapshot ledger state at each synchronization boundary, make the scorer require a successful exact-base observation before classifying no execution, and validate fault injection and response parsing across additional forge versions or providers. Such work would require a new preregistered study; no additional NIR-03 trials are authorized by this report.

## Conclusion

The evidence supports only that the corrected harness completed the stated synthetic cases on the tested Forgejo build and that the bounded model satisfied its checked properties under documented assumptions. It does not establish statistical superiority, equivalence, novelty, universal exactly-once guarantees, or production readiness. PR #29 is pushed and open for final owner acceptance.
