# Analysis plan

## Confirmatory analysis

H1 is the sole confirmatory hypothesis and maps to RQ1: paired risk difference in unsound terminal classification between retry-only and contract-aware reconciliation in the preregistered weak-endpoint schedule population with delayed settlement. The before-read versus after-absence timing contrast is secondary/exploratory. Each block replays the same fault schedule under both arms; policy assignment order is randomized. Report the paired discordant-pair table, paired risk difference, two-sided 95% confidence interval, and exact McNemar test. The proposed 650 pairs is a planning scenario for a 5 percentage-point effect at 0.20 paired discordance, not a conservative bound. Discordance is unknown; exact simulation across at least 0.10, 0.20, 0.30 and plausible missingness rates is required before registration. A blinded pooled discordance estimate may inform a predeclared sample-size adjustment without examining arm labels.

Use intention-to-treat by randomized strategy. H2–H5 are secondary mechanism/formal questions; designate their outcome families and Holm correction before preregistration. Formal counterexamples are not trial observations and are reported separately. No equivalence inference is planned. Report all assigned outcomes. Missing evidence is not deleted: primary binary outcome is “unscorable” and reported separately; sensitivity analyses give best/worst bounds by assigning all unscorable records in each direction. Unknown is a distinct protocol outcome and is not missing. Do not convert unknown to failure or success.

## Secondary and factorial outcomes

Report exact counts and intervals for wrong-digest effects, duplicate logical objects, conflict, unknown, missing evidence, and capture-integrity failure. For time-to-sound-terminal, report censoring and use survival methods only if assumptions are met. Factorial/mechanism contrasts are secondary and use a prespecified generalized linear model with policy, endpoint capability and fault schedule factors plus interactions; account for schedule/instance clustering. Use Holm correction across the designated secondary hypothesis family. Do not infer equivalence from a nonsignificant test. Equivalence would require a separate margin and powered design, which is not proposed here.

## Evidence evaluation

The independent evaluator consumes indexed treatment-facing HTTP captures, authoritative fixture commit journal/state snapshots, and immutable intent/verification inputs. It validates SHA-256 for every raw response, journal event, state snapshot, and file-level ledger snapshot; checks event IDs/barriers; and reconstructs ground-truth state at the fixed horizon from the fixture oracle, not from the treatment-facing API. HTTP 404 is an observation failure/absence at that endpoint, never proof of base state or non-execution by itself. `not_executed` requires an authoritative exact-base snapshot plus all required object/status snapshots at a known commit version. For each assignment, preserve the computed reason trace and input digest. Repeated aggregate log references to one event are deduplicated by event ID, but originals remain archived.

## Integrity checks and reporting

Before unblinding policy labels, verify assignment completeness, raw body digests, response/endpoint mapping, barrier event uniqueness and evidence retention. Keep evaluator code/version pinned, independent of driver logic; reviewers receive sanitized raw evidence and frozen scoring code. Publish all deviations and failures alongside results. No post-hoc outcome recategorization or selective omission.
