# NIR-03 supplementary exploratory protocol (S1)

**Status:** preregistered protocol; execution has not started. This protocol is separate from the retained P0.1 protocol-v2 25-trial matrix. Do not append S1 rows to or rewrite `../pilot-results.json`.

**Preregistration basis:** source branch `research/nir-03-p01`, parent P0.1 report commit `047f2ae765591c5098f9396d7d8591b0955f2a79`. Protocol must be committed before any S1 fault run. Runner changes, any deviations, and results must be recorded in this S1 directory and identified by commit SHA.

## Question

When recovery itself is repeatedly interrupted, and forge observations fail or disagree with a lost acknowledgement, does the recovery logic preserve `unknown` until authoritative reads permit exact completion or conflict classification, without duplicating effects or overwriting concurrent state?

This question targets explicit gaps in P0.1. It does not test a product implementation or compare general-purpose engineering methods.

## Environment and boundaries

Use one fresh Forgejo 17.0.2 disposable SQLite instance, verified by the signed binary and configured by `../prepare_forgejo.sh`. Bind only to loopback. Disable Actions, SSH, SMTP, external integrations, registration, and package registry. Use synthetic private repositories, generated commits, and scoped temporary credentials. Keep all instance data and token files outside the repository. Never merge or enable automatic merging. Do not access production Harness or Altruforge runtime state.

The byte-level synthetic commit and verification-identity recipe is fixed in [fixture-recipe.md](fixture-recipe.md). Before execution, freeze the S1 runner and separate observer in this directory, the TLC/runtime versions, the fault schedule, and this protocol in Git. Use a fresh output directory. Record every assigned cell, including setup failures, and retain response captures without credentials.

## Assignment matrix

One assignment per cell (14 total): seven scenarios by two recovery policies. This sample is descriptive only; there is no statistical hypothesis test, superiority/equivalence claim, or inferred rate.

Policies:

- **Contract-aware baseline:** exact remote reads and conditional ref update; it uses the same provider APIs and fault schedule as the candidate.
- **Candidate reconciliation:** the same operations plus a durable expected-effect ledger. `complete` requires every expected identity; a failed required read leaves the result `unknown`; `not_executed` requires authoritative reads to show the effect absent; `conflict` requires authoritative observation of incompatible concurrent state.

| Scenario | Fault schedule | Required classification / safety result |
| --- | --- | --- |
| R1 no effect, ref read unavailable | No publication write has been sent or applied. Return HTTP 503 for the branch observation while the PR and status reads report their actual empty state, then restore branch reads | Candidate reports `unknown` during outage; after restored branch read confirms the expected base and other reads confirm no effects, classify `not_executed`; never complete from the failed read |
| R2 PR applied, PR read unavailable | Candidate ref and exact status already exist. Forge accepts the exact PR, response is dropped; fail PR-list observation, then restore | Candidate reports `unknown` while read fails; later adopts only the exact one PR by run/base/head/SHA identity and completes only after all expected effects are observed; no duplicate |
| R3 status applied, status read unavailable | Candidate ref and exact PR already exist. Write status for exact candidate and verification identity, then fail that SHA's status read and restore | Candidate reports `unknown` during outage; later complete only after exact status is observable |
| R4 ambiguous create with observation outage | Candidate ref and status exist. Proxy forwards PR create, forge commits it, proxy drops response; make PR read fail, restore, then reconcile | Do not infer success or absence from timeout; `unknown` until exact PR is read; final exact PR count is one |
| R5 repeated interruption during recovery | Kill worker after recovery begins, up to three times: after first remote read, after first missing-effect dispatch, and before final durable classification | Every restart resumes from durable identity; incomplete observations remain `unknown`; eventual terminal result is exact `complete` or `conflict`, never a guessed completion |
| R6 remote drift plus failed ref observation | Before any publication effect, advance the ref with a competing writer, then fail the ref read; restore it after recording the outage | `unknown` while unreadable, then `conflict` when competing SHA is observed; competing ref is preserved |
| R7 multiple read failures | In separate substeps make the observer-facing ref, PR-list, and candidate-status GET return HTTP 503; restore each endpoint after capture and repeat the read | Any missing required observation blocks `complete`; retain per-endpoint failure and recovery evidence |

Run each scenario once for each policy, with separate repositories and fixed, predeclared synthetic IDs per cell. Do not replace a failed cell with a fresh successful run. No retries beyond the stated recovery schedule may be added after observing outcomes; any repair is a protocol amendment and a new separately identified run.

## Observer and oracle independence

The driver may issue mutations and schedule faults, but it must not supply the final observed branch SHA, PR identity/count/state, or status identity. Fault injection is through a loopback reverse proxy on the observer-facing URL; the observer records injected HTTP 503 responses as failures and later successful responses after the fault rule is removed. A separate observer process must query the Forgejo API directly after each recovery attempt and at terminal disposition. It records endpoint, HTTP status, returned identity fields, and a SHA-256 digest of the raw response body; omit authorization headers, tokens, and private user data. The scorer consumes only the saved observer captures and frozen assignment map, not runner `outcome`, `ledger_outcome`, or `eligible_resolution` fields.

Keep the observer's API client separate from the driver module/process. The same Forgejo instance and read credential remain a common trust boundary, and API freshness/consistency is an assumption to audit. If an endpoint cannot be read, record the transport/API error as unavailable evidence; do not synthesize a missing object or convert failure into an empty list.

## Frozen measurements and decision rules

For every cell record: protocol and tool versions; scenario/policy; exact run/base/candidate/verification identifiers; each interruption point; mutation request outcome; observer endpoint/status/body digest; final ref, exact PR count and identity, exact status identity; ledger classification; duplicate/unauthorized effects; merges; and setup/read failures.

Primary checks:

1. No `complete` without all exact remote identities in successful observer responses.
2. Any required failed observation blocks `complete` and yields `unknown` until a successful read resolves the state.
3. Repeated restarts preserve intent identity and do not create duplicate PRs or overwrite drift.
4. Conflicts are classified only from observed incompatible remote state.
5. All 14 assignments stay in the denominator; report missing cells and infrastructure errors explicitly.

A clean S1 run can demonstrate only that these specific cases behaved as specified on this Forgejo version and setup. It cannot establish statistical efficacy, equivalence, novelty, universal exactly-once behavior, or production readiness. If a read error cannot be injected at the selected API layer or the observer shares too much implementation with the driver, stop and amend the protocol before outcome runs; preserve the failed setup as setup evidence.

## Output separation

Expected artifacts, each in this directory: `runner.py`, `observer.py`, `evaluation.py`, `results.json`, `evaluation.json`, raw observer captures under an ignored/private temporary directory summarized by hashes, and `execution-notes.md`. The P0.1 matrix and its protocol/results remain byte-for-byte unchanged.
