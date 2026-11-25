# NIR-03 — Forge-backed recovery of verified candidate delivery

Status: exploratory P0.1 pilot. This study extends the NIR-02 research question; it does not claim novelty, a product implementation, or production readiness. The specification and outcome rules below were committed before confirmatory execution. The pilot is exploratory with one assigned trial per cell and cannot establish statistical efficacy.

## Question

On a real forge with documented Git ref and pull-request semantics, which recovery policies can distinguish an unexecuted publication from an applied-but-unacknowledged effect and from concurrent drift, while preserving the exact candidate commit and never completing with mismatched verification evidence?

## Scope and environment

- Forge: isolated Forgejo `17.0.2`, verified from the official binary signature; loopback only, SQLite, disposable data/repositories under `/tmp`.
- Git and Python versions are recorded in the results artifact.
- Every repository, account, task, candidate, PR, status, and local ledger used in this pilot is synthetic and disposable.
- Forgejo Actions, SMTP, SSH, registration, package registry, and remote integrations are disabled. PRs are draft. The experiment never calls merge or auto-merge APIs.
- There is no production Harness or AltruForge project state in the experiment path.

## Contract probes

Before comparing recovery policies, the pilot checks these actual Forgejo behaviors:

1. A push guarded by an explicit expected-old-object lease rejects after a competing writer advances the branch and preserves the competing commit.
2. A duplicate pull-request creation is rejected, and a read query locates the existing PR by repository, head, base, candidate SHA, and stable run marker.
3. Commit-status writes and reads are scoped to the requested immutable candidate SHA; querying a different SHA does not return the candidate's status.
4. Created PRs are drafts and remain unmerged; no automatic merge path is enabled or invoked.

These are version-specific observations, not assumptions about every forge.

## Frozen pilot design

The independent observer records forge state after every trial. Each policy receives the same generated repository state and fault assignment. There are five scenarios and five policies, one trial per cell (25 total):

| Scenario | Injection point | Eligibility |
| --- | --- | --- |
| No fault | None | Eligible |
| Before dispatch | Kill worker after durable intent and before the PR request | Eligible after recovery |
| Effect before local completion | Forge accepts PR creation; kill worker before local completion checkpoint | Eligible after recovery |
| Delayed acknowledgement | Proxy forwards PR create; forge commits it; proxy delays response beyond client timeout | Eligible after recovery |
| Remote drift | Concurrent writer advances feature ref after candidate preparation; candidate push uses expected-old ref lease | Conflict is the correct terminal outcome, not successful publication |

Recovery policies:

- **Blind retry:** resend the same PR creation once without reading remote state.
- **Checkpoint replay:** replay the persisted incomplete publication step once without remote reconciliation.
- **Fail-stop:** after an interrupted or ambiguous step, do no further external write and retain an unknown/blocked outcome.
- **Contract-aware baseline:** probe exact ref and PR state; use the forge's Git lease for conditional ref updates; adopt an existing PR only when repository, head, base, draft state, stable run marker, and candidate SHA match; attribute required status to the candidate SHA.
- **Candidate reconciliation:** use the same provider operations as the strong baseline, while persisting and checking an explicit expected-effect set (candidate branch, exact draft PR, and exact-SHA status) and classifying each recovery as `complete`, `not_executed`, `unknown`, or `conflict`.

The contract-aware baseline is intentionally strong and receives the same provider guarantees as the candidate. The exploratory question is whether the explicit effect-set ledger improves classification or resolution beyond that baseline. One-trial differences are descriptive only.

## Frozen measures and grading

Primary measures:

- **Unsafe completion:** local state says complete while the observed PR/ref/status is absent or bound to a different candidate, task, base, or repository.
- **Unauthorized/duplicate effect:** unexpected repository/ref/PR/status mutation, duplicate PR for one run, overwritten concurrent ref, or any merge.
- **Eligible resolution:** exact candidate draft PR and required exact-SHA status are observed for eligible cases.
- **Explicit unknown/conflict:** uncertain effect is reported as unknown or remote drift as conflict rather than success.

Secondary measures: recovery attempts, API/Git response, elapsed recovery time, and manual action needed. The evaluator reconstructs these measures from recorded observer state rather than trusting the runner's summary labels.

The unit of assignment is one scenario-policy trial. All assigned trials, including errors and unknowns, remain in the denominator. Do not exclude failed or inconvenient outcomes. A positive result requires a reproduced failure in an existing strategy and a reason strong provider protections or Loop Engineering-like reconciliation are insufficient. If the strong baseline closes the observed gap, report a negative/replication result and revise the question rather than claiming a novel method.

## Execution and artifacts

Run the disposable forge pilot with a verified local Forgejo instance:

```sh
python3 research/nir-03/pilot_forgejo.py \
  --base-url http://127.0.0.1:30300 \
  --token-file /path/to/private/temporary/token \
  --output research/nir-03/pilot-results.json
python3 research/nir-03/evaluate_pilot.py research/nir-03/pilot-results.json
```

The token file must remain outside Git, mode `0600`, and must not be printed. The runner refuses non-loopback URLs and requires a fresh experiment namespace. Results contain no credentials or private account data. This study does not change MVP acceptance or implement any Altruforge runtime feature.

## Results and limitations

See [pilot results](pilot-results.json) and [independent outcome evaluation](evaluation.md). One Forgejo version, Linux host, generated tasks, and one observation per cell limit generalization. The pilot does not exercise GitHub, CI jobs, process crash recovery inside a product runtime, agent verification quality, protected branch administration, or multiple Forge implementations. Any claim about those surfaces remains unverified.
