# S1-R2 execution and acceptance audit

**Replication:** S1-R2, preregistered by `S1-R2-AMENDMENT.md` at commit `3faf482563ade1c473aa83d0b8b33c3678c31d74` before the matrix was started.  
**Runner source commit recorded in results:** `3faf482563ade1c473aa83d0b8b33c3678c31d74`  
**Provider:** Forgejo `17.0.2+gitea-1.22.0`, disposable SQLite state under `/tmp/nir03-s1-r2-forgejo`, loopback port `30310`.  
**Run timestamp:** 2026-11-26 UTC.  
**Private run directory:** `/tmp/nir03-s1-r2-run-20261126/`; raw observer data is retained there and is not copied into the Git tree.

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

The checked-in `results.json` and `evaluation.json` are these output files. `raw-capture-index.json` indexes 150 observer capture documents and each raw response body by filename, endpoint, HTTP status, timestamp, byte length, and SHA-256. Raw bodies remain in the private `/tmp` capture directory. The index contains no credential material. All 14 immutable intent snapshots and 7 candidate-policy ledger snapshots are also retained under `intents/` and `candidate-ledgers/`, with hashes in `durable-state-index.json`; the original S1 `unknown` ledger records are not rewritten.

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

Totals: **14 assigned, 14 recorded, 0 missing, 0 unexpected; 10 `complete`, 2 `not_executed`, 2 `conflict`; 0 capture errors; 0 recorded protocol deviations.** Every cell's final `complete` classification had exactly one matching PR and exact status in observer data. No cell had a duplicate exact PR. The R1/R6 terminal evaluation notes that earlier outage evidence exists, even though later successful observations resolved the terminal result; the driver records `unknown` at each required failed-read boundary before its later terminal disposition. R7 records `unknown` after each failed required read before final completion.

S1-R2 also records driver/provider mutation metadata, endpoint identities, timestamps, status codes, response digests, worker barriers, and observer capture references. Captured observer bodies confirm the injected failures and later reads. The raw capture index allows body-level digest verification without storing those bodies in the repository.

## Acceptance audit

| Requirement | Result | Evidence |
| --- | --- | --- |
| Correct `GIT_CONFIG_COUNT` and audit inherited config | Pass | `git_env.py`; three tests in `tests/test_git_env.py`; smoke report v8. |
| Infrastructure smoke before registered outcomes | Pass | Separate smoke v8, three synthetic cases, separate instance/output/labels; [`smoke-v8/SMOKE-REPORT.md`](smoke-v8/SMOKE-REPORT.md). |
| Amendment committed before outcome collection | Pass | Commit `3faf482...` is recorded by the results source commit; it precedes the runner start. |
| Original 14 blocked S1 records preserved | Pass | `PREREGISTRATION.md`, S1 `results.json`, and S1 `evaluation.json` are unchanged from the pre-replication base. |
| Execute all 14 once and preserve outcomes | Pass | `results.json` has exactly the fixed 14-label matrix; no reruns or replacements. |
| Independent read-only observer and raw evidence | Pass | Separate non-admin token scopes `read:repository,read:user`; 150 captures indexed in `raw-capture-index.json`. |
| Independent evaluation | Pass | `evaluation.json`, derived from observer captures and fixed assignment map. |
| Keep P0.1 and formal artifacts unchanged | Pass | Checked against `7b7dd1408a8fbddea3fb1d0ec9db7e699e420ede`; protected artifact check passed. |
| Update PR #29 without merge | Pending network | Local branch includes this record; push was attempted but failed because `github.com` DNS resolution was unavailable. No merge was attempted. |

## Scientific limits and deviations

No action or fault-schedule protocol deviations were recorded during the 14 assignments. A post-run record audit found a **barrier logging artifact** in the R4 rows: the same single proxy `upstream_effect_committed_ack_dropped` event is repeated in the aggregate `barriers` array because that in-memory event list is appended more than once. The raw `proxy_events` array contains one POST event per R4 cell, with one timestamp, one HTTP 201 upstream response and one dropped acknowledgement; the observer independently confirms one resulting PR. The duplicate aggregate entries are preserved as emitted and are not counted as separate events. The frozen evaluator does not use barrier array multiplicity to derive outcomes. This is a reporting limitation, not a change to the preregistered scenario or fault schedule.

The replication is descriptive, with one assignment per scenario-policy cell. Outcomes do not support a statistical superiority, equivalence, general efficacy, novelty, or universal exactly-once claim. Both policies produced the same independent terminal classifications in this run; this sample does not establish equivalence. The experiment covers only the specified API schedules and Forgejo build. It does not assess production readiness or other providers.

The evaluator's `terminal_observation_complete` flag is false for R1 and R6 because the corresponding indexed capture set intentionally includes the preregistered failed observation. This is not missing terminal data: successful post-restoration terminal captures are present, and the independent terminal classifications are based on their exact observed state. Raw body files are held outside Git, so reproducing the exact observer parsing requires retaining `/tmp/nir03-s1-r2-run-20261126/captures/` alongside this indexed record.

`PREREGISTRATION.md`, P0.1 result files, and formal model-checking artifacts remain unchanged. PR #29 is not merged. The branch still must be pushed when network access to GitHub is available.
