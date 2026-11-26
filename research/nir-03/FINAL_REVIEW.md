# NIR-03 independent scientific and technical review

**Reviewed source:** `d24e3a4fb0ed9db05f8f319f022b48eaa5bdf435`

**Review method:** a separate read-only reviewer agent inspected repository artifacts, the S1-R2 result/evaluation records, the raw capture index and `/tmp` captures, R4 proxy events, formal specification/model/logs, and reproducibility notes. It did not edit files, run trials, or use orchestrator outcome labels as independent evidence.

**Disposition:** evidence supports the recorded descriptive S1-R2 outcome categories, subject to the limitations below. No comparative scientific claim is supported.

## Findings

| Review area | Finding |
| --- | --- |
| Formal model correctness | The finite TLA+ model is internally coherent with its written one-run/one-repository abstraction. TLC v1.8.0 completed the safety run over 26 distinct states and conditional liveness run over 16 distinct states with no error. The failed deadlock and unbounded-crash liveness checks and counterexample traces are retained. |
| Formal abstraction limits | One run, one candidate, one PR slot; trusted verifier inputs; durable ledger and forge effects; accurate current reads; no stale reads, permanent observation failures, multiple concurrent runs, provider/API compromise, or post-terminal external changes. Conditional liveness assumes weak fairness and that crashes stop. This does not prove implementation or production behavior. |
| Protocol adherence | S1-R2 amendment commit `3faf482...` precedes the run. All 14 fixed labels are present once; no replacement trials, new hypotheses, or changes to scenario, policy, or evaluator criteria were made. The original S1 preregistration/results remain unchanged. |
| Fault injection | Observer-facing HTTP 503 failures are captured for the prescribed endpoints. R4 `proxy_events` show one forwarded POST per cell, upstream HTTP 201, and a dropped acknowledgement, followed by the prescribed PR-read outage. R5 synchronization barriers were reached and all six worker terminations confirmed by SIGKILL. The separate v8 smoke passed before the matrix. |
| Observer independence | The observer is a separate process using a separate non-admin token scoped `read:repository,read:user`, with repository read grants. It captured actual API GET responses, raw body digests, endpoints, timestamps, and errors. The driver, observer, and fault proxy still share the same Forgejo instance/host; API freshness and server correctness are assumed. |
| Intermediate unknown and ledger evidence | Results and captures record `unknown` at required read-failure boundaries, and the runner source atomically writes an `unknown` candidate-ledger state before recovery. However, the same ledger file is overwritten at terminal classification. Checked-in ledger artifacts are final snapshots only; no separately persisted intermediate snapshot proves the disk contents at each outage boundary. This is a durable-evidence gap, not evidence that the write did not occur. |
| Evaluator correctness | The frozen evaluator derives terminal classes from observer captures and the fixed assignment map, not driver completion labels. A reviewed edge case remains: it can treat branch HTTP 404 plus empty PR/status lists as `not_executed`. A missing branch is not proof that the ref remains at base. The observed R1 cells instead include successful HTTP 200 branch reads showing the exact base SHA, so the edge case does not change the recorded R1 classifications. The evaluator and result were left frozen; this limitation is disclosed rather than retroactively changing scoring. |
| R4 duplicate aggregate barriers | The original aggregate barrier arrays contain three identical copies of the single proxy dropped-ack event per R4 row. Each underlying `proxy_events` array contains one POST/201/drop event, one timestamp; the observer sees one exact PR and one status. See `supplementary/s1-r2/r4-barrier-audit.json`. Original results remain unchanged. |
| Failed-run preservation | The original S1 14 setup-blocked assignments remain in original S1 `results.json` and were not relabeled. Initial TLC counterexamples and failed traces are retained. S1-R2 contains all assigned outcomes without replacement. Infrastructure smoke attempts v1–v8 are archived separately (including failed v1–v5); they are excluded from trial denominators. Final v7/v8 smoke reports are checked in. |
| Scientific conclusion | S1-R2 gives 10 `complete`, 2 `not_executed`, and 2 `conflict`; both policies have the same classifications in these 14 assignments. One cell per scenario-policy pairing is descriptive and cannot establish equivalence, superiority, efficacy, novelty, or generality. P0.1 likewise did not show a resolution advantage over the selected baseline. |
| Fresh-checkout reproducibility | The repository now records pinned Forgejo verification, fresh loopback setup, exact observer account/token scopes, historical runner/evaluator commands, output paths, and archive checks. Fresh setup is reproducible without prior chat or credentials. The frozen S1-R2 assignments must not be rerun. |

## Artifact verification

At review time, the prior capture index contained 150 entries: 30 JSON capture documents and 120 raw response bodies. All file sizes and SHA-256 digests matched. The credential-pattern scan found no authorization/cookie fields, credential fields, bearer-token/JWT patterns, or personal data. The checked-in raw archive was subsequently built from those exact files, with per-file hashes and archive checksum in `supplementary/s1-r2/archive/ARCHIVE-MANIFEST.json`; the archive was re-read and each member verified byte-for-byte. No redactions were required.

Original S1, P0.1, and formal artifacts were verified unchanged relative to `7b7dd1408a8fbddea3fb1d0ec9db7e699e420ede`. PR #29 is confirmed pushed and open for owner acceptance. No merge was made.

## Required interpretation

The record supports only the stated finite-model check and the observed Forgejo 17.0.2 synthetic cases. The intermediate-ledger durability gap and evaluator 404 edge case remain explicit limitations. Nothing here establishes statistical equivalence or superiority, novelty, universal exactly-once delivery, or production readiness.
