# NIR-03 P0.1 independent evaluation

## Disposition

The retained protocol-v2 Forgejo matrix is complete as an exploratory run. It does not show an outcome-resolution advantage for candidate reconciliation over the strong contract-aware baseline. Do not advance this result into a product implementation or change product scope based on this pilot.

## Recomputed outcomes

`evaluate_pilot.py` independently grades the observer fields in `pilot-results.json`; it does not import or execute the experiment runner. It recomputes completion from exact candidate PR count, observed ref SHA, candidate-SHA status attribution, and the separate conflict condition.

This means scoring is separately implemented, but the oracle capture is not an independent process: the P0.1 runner itself performed the Forgejo API reads using its orchestration credential. The evaluator cannot detect fabricated serialized observer fields. See the [oracle independence audit](ORACLE_AUDIT.md); no stronger observer-independence claim is made.

- Assignments: 25/25; five scenarios by five policies.
- Setup errors: 0; duplicate or missing cells: 0.
- Recomputed outcomes: 13 complete, 5 conflict, 7 unknown.
- Eligible exact publication outcomes (four eligible scenarios per policy): blind retry 2/4, checkpoint replay 2/4, fail-stop 1/4, contract-aware 4/4, candidate reconciliation 4/4.
- Unsafe completion: 0. Unauthorized or duplicate effects: 0. Incorrect status attribution: 0. Contract-probe failures: 0. Merge calls: 0.
- Candidate-ledger classifications observed: `complete`, `not_executed`, and `conflict`. The candidate policy did not encounter an explicit `unknown` classification in this matrix. Fail-stop produced unknown outcomes; this does not substitute for testing candidate-ledger unknown classification.

The result is a descriptive replication/negative finding against the predeclared comparison: the explicit expected-effect ledger did not improve eligible resolution over a baseline with the same strong Forgejo contracts. One trial per cell is not a statistical efficacy estimate, and the result does not establish equivalence or generalize beyond this setup.

## Provider and safety limits

The Forgejo 17.0.2 OpenAPI create-PR schema has no `draft` field. An initial `draft: true` request created an ordinary open PR. Protocol v2 was amended before its retained matrix to use ordinary, unmerged PRs in private synthetic repositories. No merge or auto-merge endpoint was called. This experiment therefore does not meet the product's Draft PR acceptance requirement and makes no claim that Altruforge supports it.

The pilot used signed Forgejo 17.0.2 on loopback, SQLite, synthetic accounts/tasks/repos, and a Linux host. It does not test GitHub, CI execution, product-process recovery, protected-branch policy, multiple forge versions, or agent verification quality.

## Reproducibility and retained setup history

The protocol-v1 contract-discovery artifact is retained separately and excluded from the v2 outcome denominator. Setup corrections and the provider-specific protocol amendment are preserved as commits on this research branch. Early setup attempts exposed version-string parsing, clone authentication, and worker invocation assumptions; the first v1 trial then stopped when a synthetic detached candidate lacked a Forge ref for status verification. The runner was corrected and the v2 protocol was amended before the retained 25-cell matrix. These development attempts are not counted as v2 trials; the v1 probe artifact and runner history remain available for audit.

The final v2 output was generated against disposable `/tmp` state with the command in `README.md`. The token stayed outside the repository. Forgejo was loopback-only with Actions and external integrations disabled. The evaluator's saved result is `evaluation.json`.

## Next research action

Close P0.1 as exploratory with no demonstrated advantage over the strong baseline. Before another implementation experiment, amend the research question and preregister a follow-up that either tests a materially different provider contract or directly exercises candidate-ledger `unknown` classification and additional independent runs. Keep draft-PR acceptance unmet until a supported provider mechanism is demonstrated. No automatic merge and no production changes.
