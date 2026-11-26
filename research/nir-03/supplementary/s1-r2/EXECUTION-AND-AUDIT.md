# S1-R2 execution and acceptance audit

**Replication:** S1-R2, preregistered by `S1-R2-AMENDMENT.md` at commit `3faf482563ade1c473aa83d0b8b33c3678c31d74` before the matrix was started.  
**Runner source commit recorded in results:** `3faf482563ade1c473aa83d0b8b33c3678c31d74`  
**Provider:** Forgejo `17.0.2+gitea-1.22.0`, disposable SQLite state under `/tmp/nir03-s1-r2-forgejo`, loopback port `30310`.  
**Run timestamp:** 2026-11-26 UTC.  
**Run directory:** `/tmp/nir03-s1-r2-run-20261126/`; raw observer captures are archived durably under `archive/` as described below.

## Environment and exact execution

The Forgejo binary was `/tmp/altruforge-nir03-forgejo/forgejo`; `--version` reported `17.0.2+gitea-1.22.0`. A fresh instance was prepared with `research/nir-03/prepare_forgejo.sh`. The owner credential and the separate non-admin observer credential remained in mode-0600 files outside Git. The observer token was issued with `read:repository,read:user`; the runner granted the observer read access to each synthetic private repository. Authenticated `/api/v1/version` returned the expected version before the run. The experimental environment did not use production Harness or Altruforge runtime state.

The single matrix invocation was:

```sh
python3 research/nir-03/supplementary/runner.py \
  --base-url http://127.0.0.1:30310 \
  --owner-token-file /tmp/nir03-s1-r2-forgejo/api-token \
  --observer-token-file /tmp/nir03-s1-r2-forgejo/observer-token \
  --capture-dir /tmp/nir03-s1-r2-run-20261126/captures \
  --output /tmp/nir03-s1-r2-run-20261126/results.json \
  --experiment-id S1-R2 \
  --protocol research/nir-03/supplementary/S1-R2-AMENDMENT.md \
  --label-prefix nir03-s1-r2 \
  --repo-prefix nir03-s1-r2
```

The frozen observer-only evaluator was then run once:

```sh
python3 research/nir-03/supplementary/evaluation.py \
  /tmp/nir03-s1-r2-run-20261126/results.json \
  --matrix-prefix nir03-s1-r2 \
  --output /tmp/nir03-s1-r2-run-20261126/evaluation.json
```

The checked-in `results.json` and `evaluation.json` are these output files. `raw-capture-index.json` indexes **150 files: 30 observer capture documents and 120 raw response bodies**, recording filename, endpoint, HTTP status, timestamp, byte length, and SHA-256. All 150 files were verified against that index before archival. The archive is [`archive/nir03-s1-r2-raw-observer-captures.tar.gz`](archive/nir03-s1-r2-raw-observer-captures.tar.gz); its SHA-256 is `31954a6564acebcd3cb4161874e9404defd80bf1a73dc239c4bf984cafeafc10`. The source index SHA-256 is recorded in [`archive/ARCHIVE-MANIFEST.json`](archive/ARCHIVE-MANIFEST.json). An automated credential scan found no authorization/cookie fields, credential fields, bearer/JWT patterns, or sensitive personal data. Email-like values are limited to synthetic test identities (`nir03-s1@example.invalid`, `researcher@localhost`, and `researcher@noreply.127.0.0.1`). No redactions were made. For access, clone/checkout this research branch, run `sha256sum -c` using the digest in the archive manifest, and extract with `tar -xzf nir03-s1-r2-raw-observer-captures.tar.gz -C <private-directory>`; see [`archive/ARCHIVE-README.md`](archive/ARCHIVE-README.md) for the manifest mapping from unchanged capture JSON to archived body files. All 14 immutable intent snapshots and 7 candidate-policy ledger snapshots are retained under `intents/` and `candidate-ledgers/`, with hashes in `durable-state-index.json`; original S1 `unknown` ledger records are not rewritten.

## Observed outcomes

The evaluator independently derived its classifications from the saved observer responses and fixed 14-label map. It did not consume driver classification labels for scoring.

| Scenario | Contract-aware | Candidate reconciliation | Independent remote evidence |
| --- | --- | --- | --- |
| R1 | `not_executed` | `not_executed` | Injected branch GET HTTP 503 was captured; restored reads showed base ref and no PR/status. |
| R2 | `complete` | `complete` | PR-list HTTP 503 was captured; restored terminal reads found exactly one matching PR and exact status. |
| R3 | `complete` | `complete` | Candidate-status GET HTTP 503 was captured; restored terminal reads found exactly one matching PR and exact status. |
| R4 | `complete` | `complete` | Forgejo returned HTTP 201 for the PR create upstream, proxy dropped the acknowledgement, observer-facing PR read returned 503, restored reads found exactly one PR and status. |
| R5 | `complete` | `complete` | All three synchronization barriers were reached and each worker termination was confirmed with SIGKILL (`-9`); recovery ended with exactly one PR and status. |
| R6 | `conflict` | `conflict` | Branch GET HTTP 503 was captured; restored read observed the competing SHA, and no PR/status was present. |
| R7 | `complete` | `complete` | Branch, PR-list, and candidate-status HTTP 503 responses were separately captured; restored terminal reads found exactly one PR and status. |

Totals: **14 assigned, 14 recorded, 0 missing, 0 unexpected; 10 `complete`, 2 `not_executed`, 2 `conflict`; 0 capture errors; 0 recorded action/fault-schedule deviations.** Every cell's final `complete` classification had exactly one matching PR and exact status in observer data. No cell had a duplicate exact PR. The R1/R6 terminal evaluation notes that earlier outage evidence exists, even though later successful observations resolved the terminal result; the driver record includes `unknown` at each required failed-read boundary before its later terminal disposition. R7 records `unknown` after each failed required read before final completion.

S1-R2 also records driver/provider mutation metadata, endpoint identities, timestamps, status codes, response digests, worker barriers, and observer capture references. Captured observer bodies confirm the injected failures and later reads. The R4 aggregate-barrier issue was audited in [`r4-barrier-audit.json`](r4-barrier-audit.json): each R4 row has three identical aggregate copies, while its underlying proxy event log has exactly one HTTP 201 create whose acknowledgement was dropped. The original results are retained unchanged.

## Acceptance audit

| Requirement | Result | Evidence |
| --- | --- | --- |
| Correct `GIT_CONFIG_COUNT` and audit inherited config | Pass | `git_env.py`; three tests in `tests/test_git_env.py`; smoke report v8. |
| Infrastructure smoke before registered outcomes | Pass | Separate smoke v8, three synthetic cases, separate instance/output/labels; [`smoke-v8/SMOKE-REPORT.md`](smoke-v8/SMOKE-REPORT.md). |
| Amendment committed before outcome collection | Pass | Commit `3faf482...` is recorded by the results source commit; it precedes the runner start. |
| Original 14 blocked S1 records preserved | Pass | `PREREGISTRATION.md`, S1 `results.json`, and S1 `evaluation.json` are unchanged from the pre-replication base. |
| Execute all 14 once and preserve outcomes | Pass | `results.json` has exactly the fixed 14-label matrix; no reruns or replacements. |
| Independent read-only observer and raw evidence | Pass | Separate non-admin token scopes `read:repository,read:user`; 30 capture documents and 120 raw response bodies indexed and archived. |
| Independent evaluation | Pass | `evaluation.json`, derived from observer captures and fixed assignment map. |
| Final independent scientific/technical review | Pass with disclosed limits | [`FINAL_REVIEW.md`](../../FINAL_REVIEW.md) records the bounded model limits, intermediate-ledger snapshot gap, evaluator HTTP-404 edge case, and R4 aggregate-log duplication. |
| Durable raw response preservation | Pass | Archive and extraction/checksum procedure in [`archive/ARCHIVE-README.md`](archive/ARCHIVE-README.md); separate infrastructure smoke history v1–v8 in [`smoke-attempts/`](smoke-attempts/README.md). |
| Keep P0.1 and formal artifacts unchanged | Pass | Checked against `7b7dd1408a8fbddea3fb1d0ec9db7e699e420ede`; protected artifact check passed. |
| Update PR #29 without merge | Pass | `d24e3a4` was pushed to PR #29's branch; PR #29 is open for owner acceptance. No merge was attempted. |

## Scientific limits and deviations

No action or fault-schedule protocol deviations were recorded during the 14 assignments. A post-run record audit found a **barrier logging artifact** in the R4 rows: the same single proxy `upstream_effect_committed_ack_dropped` event is repeated in the aggregate `barriers` array because that in-memory event list is appended more than once. The raw `proxy_events` array contains one POST event per R4 cell, with one timestamp, one HTTP 201 upstream response and one dropped acknowledgement; the observer independently confirms one resulting PR. The duplicate aggregate entries are preserved as emitted and are not counted as separate events. The frozen evaluator does not use barrier array multiplicity to derive outcomes. This is a reporting limitation, not a change to the preregistered scenario or fault schedule.

The replication is descriptive, with one assignment per scenario-policy cell. Outcomes do not support a statistical superiority, equivalence, general efficacy, novelty, or universal exactly-once claim. Both policies produced the same independent terminal classifications in this run; this sample does not establish equivalence. The experiment covers only the specified API schedules and Forgejo build. It does not assess production readiness or other providers.

The evaluator's `terminal_observation_complete` flag is false for R1 and R6 because the corresponding indexed capture set intentionally includes the preregistered failed observation. This is not missing terminal data: successful post-restoration terminal captures are present, and the independent terminal classifications are based on their exact observed state. The byte-preserving archive now retains the raw bodies required to reproduce parsing and verify response digests.

Two further analysis limits were confirmed by the independent review. First, the runner writes an intermediate candidate-ledger classification of `unknown` after a failed required read, then atomically replaces that file with the terminal ledger. Only the terminal ledger snapshots were checked in; the intermediate on-disk contents were not separately snapshotted, so their durable persistence is supported by source flow and run telemetry but lacks a preserved file-level checkpoint. Second, the frozen evaluator permits a branch GET HTTP 404 in its `not_executed` condition when PR/status lists are empty. A missing branch does not prove the ref stayed at the base. In these recorded R1 cells, independent post-restoration observations show HTTP 200 and the exact base SHA, so that edge case did not affect the R1 classifications. The evaluator and results were left unchanged to preserve the frozen scoring record.

`PREREGISTRATION.md`, P0.1 result files, and formal model-checking artifacts remain unchanged. PR #29 is open and awaits final owner acceptance.
