# NIR-03 — Forge-backed recovery of verified candidate delivery

Status: exploratory P0.1 pilot. This study extends the NIR-02 research question; it does not claim novelty, a product implementation, or production readiness. Protocol v1 was committed before provider probes. Protocol v2 was amended and committed after those version-specific probes but before the retained matrix run. The pilot is exploratory with one assigned trial per cell and cannot establish statistical efficacy.

## Question

On a real forge with documented Git ref and pull-request semantics, which recovery policies can distinguish an unexecuted publication from an applied-but-unacknowledged effect and from concurrent drift, while preserving the exact candidate commit and never completing with mismatched verification evidence?

## Scope and environment

- Forge: isolated Forgejo `17.0.2`, verified from the official binary signature; loopback only, SQLite, disposable data/repositories under `/tmp`.
- Git and Python versions are recorded in the results artifact.
- Every repository, account, task, candidate, PR, status, and local ledger used in this pilot is synthetic and disposable.
- Forgejo Actions, SMTP, SSH, registration, package registry, and remote integrations are disabled. PRs are ordinary open PRs because Forgejo 17.0.2's `CreatePullRequestOption` schema does not expose a `draft` field and its API ignored that field in the initial contract probe. They remain confined to private disposable repositories, and the experiment never calls merge or auto-merge APIs. This is a documented provider limitation, not a change to Altruforge's Draft PR product requirement.
- There is no production Harness or AltruForge project state in the experiment path.

## Contract probes

Before comparing recovery policies, the pilot checks these actual Forgejo behaviors:

1. A push guarded by an explicit expected-old-object lease rejects after a competing writer advances the branch and preserves the competing commit.
2. A duplicate pull-request creation is rejected, and a read query locates the existing PR by repository, head branch, base branch, candidate SHA, and stable run marker. Forgejo 17.0.2's `head` filter takes the branch name (not `owner:branch`).
3. Commit-status writes and reads are scoped to the requested immutable candidate SHA; querying a different SHA does not return the candidate's status.
4. Created PRs remain unmerged; no automatic merge path is enabled or invoked. The API's create schema and ignored draft field are recorded as a contract limitation.

These are version-specific observations, not assumptions about every forge.

### Versioned contract amendment before the retained matrix

Forgejo 17.0.2's local `swagger.v1.json` defines `CreatePullRequestOption` without a `draft` property. An initial create request carrying `draft: true` returned an open PR with `draft: false`; the request was therefore not a valid draft-creation mechanism. The same API schema exposes only branch-name filtering for `head`; `head=researcher:feature` returned no result while `head=feature&base=main` returned the PR. A duplicate create returned HTTP 409. The retained matrix uses open unmerged PRs in private disposable repositories, never calls merge, and queries by the supported branch/base filters. This amendment preserves the NIR-02 operation and safety questions while recording that Forgejo's API cannot satisfy the product's draft-PR requirement. No draft capability is claimed for Altruforge.

## Frozen pilot design (protocol v2)

The P0.1 runner performs provider-backed readback after every trial. Those reads call Forgejo directly, but the readback runs in the same process and with the same credential as the driver; see the [oracle audit](ORACLE_AUDIT.md). Each policy receives the same generated repository state and fault assignment. There are five scenarios and five policies, one trial per cell (25 total):

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
- **Contract-aware baseline:** probe exact ref and PR state; use the forge's Git lease for conditional ref updates; adopt an existing PR only when repository, head, base, open/unmerged state, stable run marker, and candidate SHA match; attribute required status to the candidate SHA.
- **Candidate reconciliation:** use the same provider operations as the strong baseline, while persisting and checking an explicit expected-effect set (candidate branch, exact open PR, and exact-SHA status) and classifying each recovery as `complete`, `not_executed`, `unknown`, or `conflict`.

The contract-aware baseline is intentionally strong and receives the same provider guarantees as the candidate. The exploratory question is whether the explicit effect-set ledger improves classification or resolution beyond that baseline. One-trial differences are descriptive only.

## Frozen measures and grading

Primary measures:

- **Unsafe completion:** local state says complete while the observed PR/ref/status is absent or bound to a different candidate, task, base, or repository.
- **Unauthorized/duplicate effect:** unexpected repository/ref/PR/status mutation, duplicate PR for one run, overwritten concurrent ref, or any merge.
- **Eligible resolution:** exact candidate open PR and required exact-SHA status are observed for eligible cases.
- **Explicit unknown/conflict:** uncertain effect is reported as unknown or remote drift as conflict rather than success.

Secondary measures: recovery attempts, API/Git response, elapsed recovery time, and manual action needed. The evaluator reconstructs these measures from recorded observer state rather than trusting the runner's summary labels.

The unit of assignment is one scenario-policy trial. All 25 protocol-v2 assignments, including errors and unknowns, remain in the denominator. Do not exclude failed or inconvenient outcomes. A positive result requires a reproduced failure in an existing strategy and a reason strong provider protections or Loop Engineering-like reconciliation are insufficient. If the strong baseline closes the observed gap, report a negative/replication result and revise the question rather than claiming a novel method.

## Execution and artifacts

Run the disposable forge pilot with a verified local Forgejo instance:

```sh
python3 research/nir-03/pilot_forgejo.py \
  --base-url http://127.0.0.1:30300 \
  --token-file /path/to/private/temporary/token \
  --output research/nir-03/pilot-results.json \
  --disposable-root /tmp/altruforge-nir03-fresh-run
python3 research/nir-03/evaluate_pilot.py research/nir-03/pilot-results.json
```

The token file must remain outside Git, mode `0600`, and must not be printed. The runner refuses non-loopback URLs and requires a fresh experiment namespace. Results contain no credentials or private account data. This study does not change MVP acceptance or implement any Altruforge runtime feature.

## Results and limitations

See [protocol-v2 pilot results](pilot-results.json), [protocol-v1 contract-discovery run](pilot-results-contract-discovery.json), [provider contract evidence](provider-contracts.json), [independent outcome evaluation](evaluation.md), and [execution notes](execution-notes.md). The retained matrix found no resolution advantage over the strong contract-aware baseline (4/4 versus 4/4 eligible cases). It is a negative exploratory result, not a statistical efficacy claim. The explicit candidate-ledger `unknown` class was not observed and remains a follow-up gap. One Forgejo version, Linux host, generated tasks, and one observation per cell limit generalization. The pilot does not exercise GitHub, CI jobs, process crash recovery inside a product runtime, agent verification quality, protected branch administration, or multiple Forge implementations. Any claim about those surfaces remains unverified.

## Formal specification, model check, and scientific audit

The system state and trust boundaries, immutable identities, transition semantics, crash/recovery behavior, safety invariants, conditional liveness, provider assumptions, and impossibility boundaries are in [the formal specification](formal/SPECIFICATION.md). The initial finite TLA+ model and separate safety/liveness TLC configurations are in [formal artifacts](formal/README.md). TLC was available after obtaining the official v1.8.0 JAR; the retained safety run explored 26 distinct states and the conditional liveness run explored 16, with no error. Both initial failed runs and counterexample traces are also preserved. This is bounded model checking of this abstraction, not a proof of production behavior.

The [P0.1 oracle audit](ORACLE_AUDIT.md) confirms final ref, PR, and status fields originate in direct Forgejo API read responses and the evaluator recomputes outcomes from those fields. It also records that the P0.1 observer and driver share a process/credential, so capture was not independently isolated. The separate [S1 supplementary protocol](supplementary/PREREGISTRATION.md) requires an independent observer process and covers repeated recovery interruption, explicit candidate-ledger `unknown`, read failures, and ambiguous effects. S1 is preregistered but not executed; its protocol/results are separate from the unchanged 25-trial P0.1 matrix.

[Fresh-checkout reproducibility instructions](REPRODUCIBILITY.md) pin the Forgejo release, verify its official signature and key fingerprint, create a loopback-only disposable instance and scoped temporary token, run the exact pilot/evaluation commands, and clean up temporary state. The setup helper was smoke-tested separately; this did not rerun or alter P0.1 results.

## Remaining limitations

P0.1 remains one trial per cell on Forgejo 17.0.2. It does not test stale or unavailable reads, repeated recovery crashes, multiple providers, GitHub, CI execution, or a product runtime. The model also abstracts one run and one PR slot, assumes accurate available reads and a durable local ledger, and excludes failures after terminal completion. Forgejo 17.0.2 does not support draft creation through its PR create API; observed PRs were synthetic, private, and unmerged. None of these artifacts establish novelty, superiority, equivalence, universal exactly-once delivery, or production readiness. No runtime feature or MVP acceptance requirement changed.
