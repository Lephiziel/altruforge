# Proposed primary experimental protocol — design only

**Authorization status:** not authorized; no primary trial has been executed. This document is a proposed design for separate owner and reviewer approval. It is not a preregistration.

## Study question and unit

Test how publication policy and explicit provider endpoint guarantees affect unsound terminal classifications, duplicate logical objects, artifact identity, and recovery progress under late settlement, concurrency, observation failures, and repeated crashes. The unit is an isolated publication intent in a disposable forge repository. Primary trials must not touch production or use production credentials.

## Baselines and treatment profiles

1. **Retry-only:** resend after ambiguous timeout without querying effect identity; retained as a simple baseline, not presumed safe.
2. **Contract-aware reconciliation:** observe provider state and branch behavior on documented responses before choosing retry/conflict/unknown.
3. **Durable intent recovery:** persist immutable run/candidate/verification identity before remote dispatch and recover from that record.

A saga-style compensation policy and Olive/Beldi-style transactional runtime were considered. Compensation requires provider operations and semantic reversibility that the target forge workflow does not presently guarantee; Olive/Beldi assume all relevant stateful operations are mediated through their transactional API. Neither is a fair direct baseline without changing the system boundary. Their assumptions will be recorded in endpoint qualification; a future adapter study would be separately scoped. CAS/fencing are endpoint capabilities, not policy arms. There is no unnamed candidate arm. A provider-enforced deduplication/fencing capability is an endpoint mechanism factor, not a policy arm, and is analyzed separately. The sole confirmatory contrast is retry-only versus contract-aware reconciliation; durable-intent recovery is a secondary mechanism arm and cannot be pooled into H1. All arms receive identical candidate/base/receipt inputs, permissions, and a 300-second horizon. Each may issue at most three mutation requests per operation and 20 treatment-facing observation reads per intent; oracle/journal/snapshot reads and evaluator reads are separate and do not consume that treatment budget.

Decision rules are fixed: retry-only resends an ambiguous operation without a read, up to its operation budget, then records unknown at exhaustion; contract-aware reads exact provider state and retries only after an endpoint response that the frozen contract defines as authoritative absence, records conflict on incompatible state, and records unknown when reads are stale, inconsistent, unavailable, or contractually inconclusive; durable-intent recovery first validates persisted candidate/verification identity, then reconciles exact remote effect identity and does not mutate on inconclusive evidence. Every arm stops at the common horizon or when it reaches a sound terminal classification; reaching a terminal label does not stop independent evidence collection. Denied/unused budget is recorded. Validate these rules in a blinded fixture dry run and freeze them before preregistration.

## Factorial factors and fault schedules

The confirmatory comparison focuses on retry-only versus contract-aware reconciliation under a preregistered weak endpoint contract with an accepted-but-unacknowledged delayed create. The target schedule population is equally stratified: 50% stale-success observations and 50% unavailable observations, defining an equal-weight adverse-condition estimand rather than claiming production prevalence. Settlement timing within each stratum is pre-generated and blocked; exact schedule proportions and event timing are frozen before registration. Each paired block contains one assignment under each policy, replaying the same pre-generated fault schedule; order and repository identity are randomized within block. Additional prespecified mechanism cells vary:

- publisher count: 1 or 2; same candidate versus divergent candidates;
- endpoint writes: unconditional, fast-forward-only, CAS, server-enforced fencing, atomic idempotency-key deduplication;
- settlement: before read, between read and retry, after retry, after terminal decision;
- observations: linearizable, monotonic-versioned, stale-success, inconsistent cross-endpoint, 404, 5xx, timeout;
- recovery interruptions: crash before intent, after intent, after dispatch, after remote settle/before ack, during recovery read, after classification; repeated interruption at each boundary with synchronization barriers;
- identity: immutable digest/commit-bound request versus mutable branch-name-only request;
- verification: matching receipt and artifact. Deliberate mismatched-verifier inputs are excluded unless the verifier behavior is independently specified and validated; the current formal model does not model verifier compromise or malformed attestations.

Only legal combinations supported by a disposable provider fixture are run. Endpoint capability must be validated by isolated setup checks excluded from trial outcomes. Each distinct fault event gets a unique event ID; aggregate log rows are never counted as independent events.

## Randomization, blocking and reproducibility

Before execution, freeze source commit, provider/container digest, fixture recipe, endpoint contract, event schedules, runner, evaluator, seed, and exclusions. Generate assignments from a published seed. Randomize policy within paired schedule blocks; randomize run order and repository identity. Use fresh isolated repositories per assignment and a fixed provider reset procedure. Record UTC wall clock plus monotonic sequence/time, request IDs, endpoint, status, body digest, and synchronization barrier IDs. Store environment inventory and exact commands.

## Independent oracle

Treatment-facing observations come from an observer process with its own read-only credential and least repository scope. It captures raw HTTP status, non-secret headers, response bytes, digest, endpoint, timestamp, pagination, and errors. These API responses are not ground truth when the API may be stale. The independent oracle instead reads a fixture-side append-only commit/audit journal at the provider mutation boundary plus versioned authoritative state snapshots for ref, review object, and status. The journal is exposed read-only to an oracle process that cannot access driver labels or mutate provider state; each event identifies request, operation, commit sequence, resulting identity, and committed version. Before trial approval, freeze the journal/snapshot schema and run a separate smoke reconciliation that compares event IDs, sequence/version ordering, exact ref/object/status identities and snapshot hashes against direct fixture storage; demonstrate that observer reads and journaling do not change fixture semantics. Preserve raw oracle responses as well as normalized records. A fixture smoke check must reconcile journal events against direct storage snapshots. If the provider cannot expose a trustworthy independent commit-point oracle without changing semantics, stale-read treatment cells are not run and no soundness outcome is claimed for them. Hash journal/snapshot files and preserve them separately from treatment observations. A second checker independently derives classifications from oracle evidence. Shared host/provider dependencies are disclosed.

## Outcomes

**Primary outcome:** per-intent unsound terminal classification (binary), where complete/not_executed/conflict is scored against the independent oracle at the preregistered observation horizon; unknown is correct when evidence cannot decide. Predefine how later settlement after horizon is handled: primary horizon classification and separate late-settlement outcome, never retroactive recoding.

**Secondary:** unauthorized/wrong-digest mutation; logical objects per intent; duplicate effects; conflicts detected; terminal unknown rate; time to sound terminal state; recovery attempts; crash count tolerated; evidence completeness. Physical requests and logical provider effects are separate metrics.

## Trial counts and justification

For the single confirmatory contrast (retry-only versus contract-aware, weak endpoint profile), plan **650 paired fault-schedule blocks**, one assignment per policy in each block (1,300 total intents). The meaningful difference is a 5 percentage-point absolute risk difference in unsound terminal classification. Under a planning scenario of paired discordance probability 0.20, the McNemar normal approximation gives about 628 pairs for 80% power at two-sided alpha .05; 650 is provisional. This discordance value is not a conservative bound. Before registration, a frozen simulation across at least 0.10, 0.20, and 0.30 discordance and plausible missingness must verify power and fix allocation. Any sample-size revision occurs before treatment labels are unblinded and is documented. This is not a rare-event assurance claim; zero violations in 650 paired runs does not prove safety. A multiplicity-controlled secondary factorial study gets its own simulation and minimum detectable effects; no underpowered cells are confirmatory. If fixture capacity cannot support the count, redesign before registration.

The primary estimand is paired risk difference across schedule blocks; analyze discordant pairs with exact McNemar test and a paired risk-difference interval, with block-bootstrap sensitivity analysis. Provider-instance clustering is handled by a prespecified cluster bootstrap or mixed model when multiple instances are used. If only one instance is available, inference is conditional on that instance and cannot generalize across providers. Exact power code/method and horizon must be attached to the future preregistration.

## Unknowns, missingness and retention

Unknown is a valid outcome category and will never be imputed as success/failure. Missing raw evidence makes the primary classification unscorable; retain the assignment as missing/failed evidence and report counts by arm. No replacement trials. Retain every assigned record including fixture failures, blocked cases, crashes, unexpected effects and evaluator errors in a durable private raw archive; publish sanitized derived records and a cryptographic manifest. Preserve file-level snapshots of each intermediate ledger state with sequence number, timestamp, previous-snapshot digest, content digest, and write acknowledgement. Keep raw HTTP body and response digest; secret values are filtered before durable capture with redaction metadata and never entered in public artifacts.

## Stopping and exclusions

Stop only for safety/security exposure, provider instability violating a frozen fixture invariant, or a preregistered integrity failure. Retain and label affected assignments; do not replace them. Exclude an assignment from primary outcome only for a predeclared infrastructure failure before treatment starts, and report it in the flow table. Any post-start failure stays in the denominator with its outcome/missingness status. No outcome-driven stopping, retries, or protocol modification.
