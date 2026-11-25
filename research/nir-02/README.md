# NIR-02 — Crash-consistent delivery of verified artifacts

Exploratory research record, 2026-11-25. The literature review is targeted and the pilot exercises local Git. Novelty remains an open question.

## Candidate research question

Under which observable and enforceable Git/forge contracts can a coding-agent delivery workflow recover after an interruption while preserving the identity of its independently verified candidate, preventing unauthorized changes, and distinguishing completed, incomplete, and indeterminate external effects?

Working title: *Crash-consistent delivery of verified software artifacts in autonomous coding-agent workflows*.

## Closest prior work

| Source | Established prior art | Boundary to investigate (not a novelty claim) |
| --- | --- | --- |
| [Loop Engineering](https://arxiv.org/html/2611.18571), preprint | Version-bound approval, durable markers, Git/CI state reconstruction, probe-before-write, observed stale-head rejection | Authors explicitly report no controlled interruption experiment establishing recovery correctness or convergence |
| [LIMBO](https://arxiv.org/html/2609.29095), preprint | Tool contracts, late commits, read-back limitations, impossibility result | Apply and test limits in coupled Git/forge workflows, not rediscover the theorem |
| [Idempotency Is Not Recovery](https://arxiv.org/html/2611.23353), preprint v2 | Intent ledger, reconciliation, sealed evidence, controlled local failure testing | Multi-endpoint Git/forge workflow and version-specific acceptance |
| [Atomix](https://arxiv.org/html/2602.14849), preprint | Transactional effect scopes, compensation, fail-stop and partial commit reporting | Semantic validation and version-bound delivery; no claim of atomic externalization over arbitrary endpoints |
| [AgentFaultBench](https://arxiv.org/html/2611.20711), preprint | State-verified tool-fault experiments in isolated GitLab | Actual process termination and Git candidate identity; source and complete traces not public with submission |
| [Crab](https://arxiv.org/html/2604.28138), preprint | Agent sandbox checkpoint/restore | Remote Git and forge effects beyond a local snapshot |
| [AgentRewind](https://arxiv.org/html/2608.14380), preprint | Joint workspace and context rollback | External network effects are not restored; Git internals excluded from tracked snapshots |
| [Resume Means Resume](https://arxiv.org/abs/2608.03836), preprint | Workflow persistence conformance, concurrent checkpoint consumption races | Domain-specific contract for Git artifact delivery |
| [AgentChaos](https://conf.researchr.org/details/ase-2026/ase-2026-research-track/141/AgentChaos-Chaos-Engineering-for-Agent-Systems-via-Programmatic-Fault-Injection), ASE 2026 | Nonintrusive runtime LLM API fault injection | Delivery-step and orchestrator crash injection |
| [Beldi](https://www.usenix.org/conference/osdi20/presentation/zhang-haoran), OSDI 2020 | Logged transactional serverless workflow execution | External forge operations with weaker or heterogeneous contracts |
| [Durable Functions](https://www.microsoft.com/en-us/research/publication/durable-functions-semantics-for-stateful-serverless/), OOPSLA 2021 | Durable workflow replay semantics | Preserve nondeterministic agent outputs as immutable activity results |
| [Anvil](https://www.usenix.org/conference/osdi24/presentation/sun-xudong), OSDI 2024 | Formal verification of eventually stable reconciliation | Explicit application-specific safety and conditional liveness over Git/forge effects |
| [in-toto](https://www.usenix.org/conference/usenixsecurity19/presentation/torres-arias), USENIX Security 2019 | Artifact-bound supply-chain evidence | Reconcile provenance with live external state; cryptographic binding alone does not prove semantic correctness |

Primary technical contracts: [Git push](https://git-scm.com/docs/git-push), [GitHub PR REST API](https://docs.github.com/en/rest/pulls/pulls), [GitHub protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches), [GitHub Checks API](https://docs.github.com/en/rest/guides/using-the-rest-api-to-interact-with-checks). Do not assume identical semantics across forges. In particular, test existing PR uniqueness, read visibility, CAS, and check attribution before choosing fault cases.

## Initial hypotheses (not validated)

- H1: preserving a candidate's immutable identity across restart and reconciling remote state reduces stale-evidence and wrong-artifact completion relative to matched retry/checkpoint baselines.
- H2: contract-aware recovery resolves a greater share of resolvable operations than fail-stop alone without increasing observed safety violations; ambiguous effects remain explicitly unknown.
- H3: any safe automatic recovery guarantee is conditional on documented endpoint semantics; no unrestricted exactly-once claim.

## Candidate invariants and definitions

- Success is tied to the exact repository, task, immutable candidate commit, relevant base/merge revision, policy and verification context, and observed PR identity. Passing a test is not proof of semantic correctness.
- Never publish or mark successful using mismatched verification evidence; distinguish observed success at a defined transition from continuous future validity.
- Do not overwrite unrelated changes or repeat an ambiguous non-idempotent operation without a contract that makes it safe.
- Liveness is conditional on eventual availability, stable desired state, adequate observation and settlement contracts, finite injected failures, and fair scheduling.
- Distinguish verified complete, verified not executed, unknown, conflict and blocked. Blocked is not successful.

## Exploratory Git-only pilot (executed)

Run the pilot from the repository root with Python 3 and Git installed.

```sh
python3 research/nir-02/pilot_git.py
```

The script creates temporary local repositories. [Recorded output](pilot-results.json) includes the actual Git, Python, and platform versions.

- A push updates the remote ref to the intended commit while the local ledger retains the pending intent.
- A second clone advances the remote ref. An ordinary push is rejected with `fetch first`, and the push with an explicit stale lease is rejected with `stale info`. Both leave the new remote commit intact.

The script models missing acknowledgement by omitting the local completion update after a successful push. It uses a fixture commit and exercises local Git only. Process termination, network faults, PRs, CI, independently verified patches, and agent execution remain outside this pilot.

## Next experiment: P0.1 (not run)

Use a disposable local forge (e.g. Forgejo, chosen after contract checks) and an independent observer. Pin versions and use identical pre-generated candidate patches. First establish actual operation contracts: push CAS, PR uniqueness and lookup, check attribution. Then compare matched retry, checkpoint, read-back + native conditional/idempotent operations, fail-stop, and candidate reconciliation. Compare a strong contract-aware baseline with the candidate using the same provider guarantees. Inject before dispatch, after confirmed remote effect but before durable completion, delayed acknowledgement, and remote drift. Verify that a fault actually occurred. Include no-fault runs. Capture independent remote state and effect history, not only final output. Primary measures: unsafe completion, unauthorized effects, successful resolution among eligible cases, explicit unknowns; secondary: recovery time and manual intervention. Freeze scenarios, policies and grading before confirmatory runs; count all assigned trials, including unknown outcomes. No automatic merge or production repositories.

## Stop/go gate

Advance to protocol implementation only after reproducing at least one concrete failure in a reasonable existing strategy with real Git/forge semantics and showing why existing built-in protections and Loop Engineering-like policies are insufficient or insufficiently evaluated. A negative result or replication study is acceptable. If the gap is closed by prior work, revise the question instead of manufacturing a weak baseline. The product boundaries for this research are [durable run state](../../docs/tasks/MVP-04.md), [independent verification](../../docs/tasks/MVP-11.md), and [Draft PR publication](../../docs/tasks/MVP-12.md). Each task has its own acceptance evidence.
